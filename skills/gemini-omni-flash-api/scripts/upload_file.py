#!/usr/bin/env python3
"""Gemini Files API upload utility with polling, dry-run validation, and secret redaction.

Uploads local media files (images, videos, audio, documents) to the Gemini Files API via
the official `google-genai` SDK and polls until processing reaches the `ACTIVE` state.
Supports standalone CLI execution (`--name`, `--no-wait`, `--dry-run`) as well as
programmatic import from `scripts/video/generate_video.py`.
"""

import argparse
import json
import logging
import mimetypes
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.parse

from google import genai
from google.genai import errors, types

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from video import config  # noqa: E402

logger = logging.getLogger(__name__)


def get_api_key():
    """Retrieves the Gemini API key from the configured environment variable."""
    return os.environ.get(config.GEMINI_API_KEY_ENV)


def strip_query_params(url):
    """Strips query parameters from a URL for clean logging and secret safety."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query=""))


def sanitize_error(err):
    """Sanitizes error strings by redacting API keys, tokens, internal hosts, and raw bodies."""
    if not err:
        return ""

    if isinstance(err, errors.APIError):
        parts = []
        if getattr(err, "code", None):
            parts.append(str(err.code))
        if getattr(err, "status", None):
            parts.append(f"({err.status})")
        if getattr(err, "message", None):
            parts.append(f": {err.message}")
        elif getattr(err, "details", None):
            parts.append(f": {err.details}")
        err_str = " ".join(parts) if parts else str(err)
    else:
        err_str = str(err)

    key = get_api_key()
    if key and len(key) >= config.MIN_REDACT_KEY_LENGTH:
        err_str = err_str.replace(key, "[REDACTED_KEY]")

    err_str = re.sub(r"AIza[0-9A-Za-z_\-]{30,}", "[REDACTED_KEY]", err_str)
    err_str = re.sub(r"AQ\.[0-9A-Za-z_\-]{20,}", "[REDACTED_KEY]", err_str)
    err_str = re.sub(r"ya29\.[0-9A-Za-z_\-]+", "[REDACTED_TOKEN]", err_str)
    err_str = re.sub(
        r"Bearer\s+[A-Za-z0-9_\-\.]+",
        "Bearer [REDACTED_TOKEN]",
        err_str,
        flags=re.IGNORECASE,
    )
    err_str = re.sub(
        r"([?&](?:key|api_key|apiKey|access_token|auth|signature)=)[^&\s\"'<>()]+",
        r"\1[REDACTED]",
        err_str,
    )
    err_str = re.sub(
        r"https?://[a-zA-Z0-9.\-_]*\.corp\.goog[^\s\"'<>)]*",
        "[INTERNAL_HOST]",
        err_str,
    )
    err_str = re.sub(
        r"https?://[a-zA-Z0-9.\-_]*\.sandbox\.googleapis\.com[^\s\"'<>)]*",
        "[SANDBOX_ENDPOINT]",
        err_str,
    )
    err_str = re.sub(
        r"https?://(?:generativelanguage|aiplatform)\.googleapis\.com/v[0-9a-z_]+/",
        "[API_ENDPOINT]/",
        err_str,
    )
    err_str = re.sub(
        r"\bbody\s*=.*\Z",
        "body=[REDACTED_BODY]",
        err_str,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if (
        "<html" in err_str.lower()
        or "<!doctype" in err_str.lower()
        or "<body" in err_str.lower()
    ):
        title_match = re.search(r"<title>(.*?)</title>", err_str, re.IGNORECASE)
        if title_match:
            err_str = f"HTTP Error Response: {title_match.group(1).strip()}"
        else:
            err_str = re.sub(r"<[^>]+>", " ", err_str)

    err_str = re.sub(r"\s+", " ", err_str).strip()
    if len(err_str) > config.MAX_SANITIZED_ERROR_LENGTH:
        cutoff = config.MAX_SANITIZED_ERROR_LENGTH - len(config.TRUNCATION_ELLIPSIS)
        err_str = err_str[:cutoff] + config.TRUNCATION_ELLIPSIS

    return err_str


def detect_mime_type(file_path):
    """Determines MIME type from file extension, falling back to `mimetypes.guess_type`."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }

    if ext in mime_map:
        return mime_map[ext]

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    return "application/octet-stream"


def _terminate_process_group(proc):
    """Terminates a subprocess and its entire session/process group safely."""
    if proc.poll() is not None:
        return
    if hasattr(os, "killpg"):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        proc.kill()
    proc.wait()


def _run_prep_video_subprocess(cmd, timeout_seconds):
    """Runs `prep_video.py` in a dedicated process group so timeouts kill child `ffmpeg` processes."""
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        return proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(proc)
        raise RuntimeError(
            f"Error: prep_video.py timed out after {timeout_seconds}s."
        ) from exc
    finally:
        _terminate_process_group(proc)


def upload_file(file_path, display_name=None, interactive=None, dry_run=False):
    """Uploads a local file via `google-genai` SDK with optional large-video pre-processing."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Error: File '{file_path}' not found.")

    file_size = os.path.getsize(file_path)
    mime_type = detect_mime_type(file_path)
    resolved_display_name = display_name or os.path.basename(file_path)

    logger.info(
        "upload_file invoked: file_path=%s display_name=%s size_bytes=%d mime_type=%s dry_run=%s",
        file_path,
        resolved_display_name,
        file_size,
        mime_type,
        dry_run,
    )

    if dry_run:
        return {
            "dry_run": True,
            "name": f"files/dry-run-{os.path.basename(file_path)}",
            "displayName": resolved_display_name,
            "filePath": os.path.abspath(file_path),
            "sizeBytes": file_size,
            "mime_type": mime_type,
            "mimeType": mime_type,
            "uri": f"{config.FILES_API_BASE_URL.rstrip('/')}/dry-run-{os.path.basename(file_path)}",
        }

    if not get_api_key():
        raise RuntimeError(
            f"Error: {config.GEMINI_API_KEY_ENV} environment variable is not set."
        )

    if interactive is None:
        interactive = bool(
            sys.stdin
            and sys.stdin.isatty()
            and threading.current_thread() is threading.main_thread()
        )

    is_video = mime_type.startswith("video/")
    if is_video and file_size > config.LARGE_VIDEO_WARN_BYTES:
        size_mb = file_size / config.BYTES_PER_MB
        print(f"\nWARNING: Video file '{file_path}' is very large ({size_mb:.2f} MB)!")
        print(
            "Note: Gemini Omni Flash is optimized for source videos at 720p and 24fps. Uploading very large or"
        )
        print(
            "high-resolution videos will significantly increase upload times and may cause Out-Of-Memory (OOM) errors."
        )

        if interactive:
            print(
                "\nWould you like to automatically pre-process this video first using prep_video.py?"
            )
            print(
                "This will trim, scale, and optimize the video to ensure a fast, OOM-safe upload."
            )
            try:
                choice = input("Pre-process video? [Y/n]: ").strip().lower()
                if choice in ("", "y", "yes"):
                    prepped_output_path = os.path.join(
                        config.DEFAULT_BATCH_OUTPUT_DIR,
                        f"prepped_{os.path.basename(file_path)}",
                    )
                    os.makedirs(config.DEFAULT_BATCH_OUTPUT_DIR, exist_ok=True)

                    prep_script = os.path.join(SCRIPTS_DIR, "video", "prep_video.py")
                    if not os.path.exists(prep_script):
                        prep_script = os.path.join(SCRIPTS_DIR, "prep_video.py")

                    cmd = [
                        sys.executable,
                        prep_script,
                        file_path,
                        "--output",
                        prepped_output_path,
                    ]
                    logger.info("Executing video pre-processing subprocess: %s", cmd)
                    print(f"Running: {' '.join(cmd)}")

                    try:
                        returncode = _run_prep_video_subprocess(
                            cmd, config.PREP_VIDEO_SUBPROCESS_TIMEOUT_SECONDS
                        )
                        if returncode == 0 and os.path.exists(prepped_output_path):
                            file_path = prepped_output_path
                            file_size = os.path.getsize(file_path)
                            if not display_name:
                                resolved_display_name = os.path.basename(file_path)
                            print(
                                f"\nPre-processing completed successfully! Proceeding with upload of prepped video ({file_size / config.BYTES_PER_MB:.2f} MB)..."
                            )
                        else:
                            raise RuntimeError(
                                "Error: Video pre-processing failed. Proceeding with original file upload is not recommended."
                            )
                    except RuntimeError:
                        raise
                    except Exception as exc:
                        raise RuntimeError(
                            f"Error executing prep_video.py: {sanitize_error(exc)}"
                        ) from exc
                else:
                    proceed_choice = (
                        input(
                            "Do you want to proceed with uploading the original large video anyway? [y/N]: "
                        )
                        .strip()
                        .lower()
                    )
                    if proceed_choice not in ("y", "yes"):
                        raise RuntimeError(
                            "Upload cancelled by user. Please pre-process the video manually first."
                        )
            except (KeyboardInterrupt, EOFError) as exc:
                raise RuntimeError(
                    "\nNo input received. Upload cancelled to prevent OOM."
                ) from exc
        else:
            if file_size > config.NON_INTERACTIVE_MAX_VIDEO_BYTES:
                err_msg = (
                    f"Error: Video file is extremely large ({size_mb:.2f} MB) and script is running in non-interactive mode.\n"
                    "To prevent Out-Of-Memory (OOM) errors, upload has been blocked.\n"
                    "Please pre-process the video first using prep_video.py."
                )
                raise RuntimeError(err_msg)
            print("Proceeding with upload in non-interactive mode...", file=sys.stderr)

    print(
        f"Preparing upload of '{file_path}' ({file_size} bytes, type: {mime_type})..."
    )

    client = genai.Client(
        http_options=types.HttpOptions(timeout=config.UPLOAD_HTTP_TIMEOUT_MS)
    )

    print("Uploading file bytes using google-genai SDK...")
    try:
        upload_cfg = types.UploadFileConfig(
            display_name=resolved_display_name,
            mime_type=mime_type,
        )
        file_obj = client.files.upload(file=file_path, config=upload_cfg)
        file_dict = json.loads(file_obj.model_dump_json())
        if "uri" in file_dict and file_dict["uri"]:
            file_dict["uri"] = strip_query_params(file_dict["uri"])
        if "mime_type" in file_dict:
            file_dict["mimeType"] = file_dict["mime_type"]
        logger.info(
            "Files API upload created: name=%s uri=%s mime_type=%s size_bytes=%d",
            file_dict.get("name"),
            file_dict.get("uri"),
            mime_type,
            file_size,
        )
        return file_dict
    except errors.APIError as exc:
        raise RuntimeError(
            f"API Error uploading file via SDK: {sanitize_error(exc)}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Error uploading file via SDK: {sanitize_error(exc)}"
        ) from exc


def wait_for_active(
    file_name,
    poll_interval=config.FILE_POLL_INTERVAL_SECONDS,
    max_attempts=config.FILE_POLL_MAX_ATTEMPTS,
    backoff_factor=config.FILE_POLL_BACKOFF_FACTOR,
    max_interval=config.FILE_POLL_MAX_INTERVAL_SECONDS,
    max_timeout=config.FILE_POLL_MAX_TIMEOUT_SECONDS,
):
    """Polls the Gemini Files API until `file_name` reaches `ACTIVE` or fails/times out."""
    if not get_api_key():
        raise RuntimeError(
            f"Error: {config.GEMINI_API_KEY_ENV} environment variable is not set."
        )

    logger.info(
        "Polling file status: file_name=%s poll_interval=%s max_attempts=%d max_timeout=%ds",
        file_name,
        poll_interval,
        max_attempts,
        max_timeout,
    )
    print(f"Waiting for file {file_name} to finish processing...")

    client = genai.Client(
        http_options=types.HttpOptions(timeout=config.POLL_HTTP_TIMEOUT_MS)
    )
    attempt = 0
    current_interval = poll_interval
    consecutive_errors = 0
    max_consecutive_errors = config.FILE_POLL_MAX_CONSECUTIVE_ERRORS
    start_time = time.time()

    while attempt < max_attempts:
        if time.time() - start_time > max_timeout:
            raise TimeoutError(
                f"Error: Maximum timeout ({max_timeout}s) reached waiting for file {file_name} to become ACTIVE."
            )

        try:
            file_obj = client.files.get(name=file_name)
        except errors.APIError as exc:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                raise RuntimeError(
                    f"Error: Too many consecutive API errors checking status ({sanitize_error(exc)}). Exiting."
                ) from exc

            print(
                f"Warning: API error checking status ({sanitize_error(exc)}). Retrying in {current_interval:.1f}s..."
            )
            time.sleep(current_interval)
            current_interval = min(current_interval * backoff_factor, max_interval)
            attempt += 1
            continue
        except Exception as exc:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                raise RuntimeError(
                    f"Error: Too many consecutive errors checking status ({sanitize_error(exc)}). Exiting."
                ) from exc

            print(
                f"Warning: Error checking status ({sanitize_error(exc)}). Retrying in {current_interval:.1f}s..."
            )
            time.sleep(current_interval)
            current_interval = min(current_interval * backoff_factor, max_interval)
            attempt += 1
            continue

        consecutive_errors = 0
        state = file_obj.state
        state_str = state.name if hasattr(state, "name") else str(state)

        if state == types.FileState.ACTIVE or state_str == "ACTIVE":
            logger.info("File reached ACTIVE state: file_name=%s attempts=%d", file_name, attempt + 1)
            print("File is ACTIVE and ready for generations!")
            file_dict = json.loads(file_obj.model_dump_json())
            if "uri" in file_dict and file_dict["uri"]:
                file_dict["uri"] = strip_query_params(file_dict["uri"])
            if "mime_type" in file_dict:
                file_dict["mimeType"] = file_dict["mime_type"]
            return file_dict
        if state == types.FileState.FAILED or state_str == "FAILED":
            err_details = getattr(file_obj, "error", None)
            err_msg = f"Error: File processing failed on backend for '{file_name}' (State: FAILED)"
            if err_details:
                err_msg += f": {sanitize_error(err_details)}"
            raise RuntimeError(err_msg)

        print(f"Current state: {state_str}. Retrying in {current_interval:.1f}s...")
        time.sleep(current_interval)

        current_interval = min(current_interval * backoff_factor, max_interval)
        attempt += 1

    raise RuntimeError(
        f"Error: Maximum polling attempts ({max_attempts}) reached. File is still not ACTIVE."
    )


class SanitizedArgumentParser(argparse.ArgumentParser):
    """Custom `ArgumentParser` that sanitizes error output to prevent secret leaks."""

    def error(self, message):
        """Prints sanitized CLI argument errors to `stderr` and exits with status 2."""
        sanitized_msg = sanitize_error(message)
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {sanitized_msg}\n")


def main():
    """CLI entry point for uploading files to the Gemini Files API."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stderr,
        )

    parser = SanitizedArgumentParser(
        description="Upload files to Gemini Files API using google-genai SDK."
    )
    parser.add_argument("file", help="Path to the file to upload")
    parser.add_argument("--name", help="Custom display name for the file")
    parser.add_argument(
        "--no-wait", action="store_true", help="Don't wait for ACTIVE status"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local file metadata without calling the Gemini Files API",
    )

    args = parser.parse_args()
    logger.info(
        "CLI upload_file.main invoked: file=%s name=%s no_wait=%s dry_run=%s",
        args.file,
        args.name,
        args.no_wait,
        args.dry_run,
    )

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        try:
            file_meta = upload_file(args.file, args.name, dry_run=True)
            print("[DRY RUN] File upload validated (no API call executed):")
            print(json.dumps(file_meta, indent=2))
            sys.exit(0)
        except Exception as exc:
            print(f"Error: {sanitize_error(exc)}", file=sys.stderr)
            sys.exit(1)

    if not get_api_key():
        print(
            f"Error: {config.GEMINI_API_KEY_ENV} environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        file_meta = upload_file(args.file, args.name)
        file_name = file_meta.get("name")

        print("File metadata created:")
        print(f"  Name: {file_name}")
        print(f"  URI:  {strip_query_params(file_meta.get('uri'))}")
        print(f"  Type: {file_meta.get('mimeType')}")

        if not args.no_wait:
            file_meta = wait_for_active(file_name)

        logger.info("CLI upload_file.main completed: name=%s", file_name)
        print("\nFile upload successfully completed! JSON Output:")
        print(json.dumps(file_meta, indent=2))
        sys.exit(0)
    except Exception as exc:
        logger.error("CLI upload_file.main failed: %s", sanitize_error(exc))
        print(f"Error: {sanitize_error(exc)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
