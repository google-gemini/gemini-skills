#!/usr/bin/env python3
"""Generates, extends, and edits videos using Gemini Omni 1.2 Flash (`gemini-omni-1.2-flash`).

Uses the official `google-genai` Interactions API and Files API to perform:
  - Text-to-video generation (3s–15s, default 10s)
  - First-frame image-to-video generation (3s–15s)
  - First-and-last-frame keyframe interpolation (3s–10s) and seamless loops
  - Reference-to-video (R2V) generation with reference images (up to 6) and reference videos (new generation only)
  - Video extensions (3s–15s per turn, up to 40s total) with optional reference images
  - Single-turn and multi-turn (`previous_interaction_id`) video editing with optional reference images
  - Parallel batch execution (`--batch` JSON or `--prompts-file`) with single-instance locking
  - Offline payload validation (`--dry-run`) without spending API quota
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback (Windows)
    fcntl = None

from google import genai
from google.genai import errors, types

# Ensure stdout is line-buffered for real-time progress output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

VIDEO_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT_DIR = os.path.dirname(VIDEO_SCRIPT_DIR)
for _candidate_dir in (VIDEO_SCRIPT_DIR, SCRIPTS_ROOT_DIR):
    if _candidate_dir not in sys.path:
        sys.path.insert(0, _candidate_dir)

import config as video_config_mod  # noqa: E402
from config import (  # noqa: E402
    BATCH_LOCK_FILE_PATH,
    BATCH_LOG_PROMPT_LENGTH,
    DEFAULT_ASPECT_RATIO,
    DEFAULT_BATCH_CONCURRENCY,
    DEFAULT_BATCH_OUTPUT_DIR,
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_PATH,
    FFMPEG_STRIP_AUDIO_TIMEOUT_SECONDS,
    GEMINI_API_KEY_ENV,
    MAX_15S_REF_VIDEOS,
    MAX_BATCH_CONCURRENCY,
    MAX_DURATION_SECONDS,
    MAX_KEYFRAME_DURATION_SECONDS,
    MAX_LOGGED_PROMPT_LENGTH,
    MAX_RECOMMENDED_REF_VIDEOS,
    MAX_REF_IMAGES,
    MAX_SANITIZED_ERROR_LENGTH,
    MAX_SLUG_LENGTH,
    MAX_TOTAL_EXTENDED_SECONDS,
    MIN_DURATION_SECONDS,
    MIN_REDACT_KEY_LENGTH,
    SHORT_LOG_PROMPT_LENGTH,
    SUPPORTED_ASPECT_RATIOS,
    SUPPORTED_RESOLUTIONS,
    SUPPORTED_TASKS,
    TEMP_STRIPPED_PREFIX,
)
from upload_file import upload_file, wait_for_active  # noqa: E402

logger = logging.getLogger("gemini_omni_generate_video")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Module-level single-instance lock file descriptor kept open for process lifetime
_BATCH_LOCK_FD = None

# Thread-safe cache and per-key locks preventing duplicate Files API uploads across batch workers
_ASSET_UPLOAD_LOCK = threading.Lock()
_ASSET_CACHE = {}
_ASSET_KEY_LOCKS = {}

_BARE_FILE_HANDLE_RE = re.compile(r"^files/([A-Za-z0-9_\-]+)$")


def _get_files_api_base_url():
    """Returns the configured Files API base URL without trailing slash."""
    return video_config_mod.FILES_API_BASE_URL.rstrip("/")


def get_api_key():
    """Retrieves the Gemini API key strictly from the GEMINI_API_KEY environment variable."""
    return os.environ.get(GEMINI_API_KEY_ENV)


def strip_query_params(url):
    """Strips query parameters from a URL for clean logging and secret protection."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query=""))


def redact_secrets(text):
    """Redacts API keys, OAuth/Bearer tokens, secret query params, and internal hosts without clamping length."""
    if text is None:
        return ""
    redacted = str(text)

    key = get_api_key()
    if key and len(key) >= MIN_REDACT_KEY_LENGTH:
        redacted = redacted.replace(key, "[REDACTED_KEY]")

    redacted = re.sub(r"AIza[0-9A-Za-z_\-]{30,}", "[REDACTED_KEY]", redacted)
    redacted = re.sub(r"AQ\.[0-9A-Za-z_\-]{20,}", "[REDACTED_KEY]", redacted)
    redacted = re.sub(r"ya29\.[0-9A-Za-z_\-]+", "[REDACTED_TOKEN]", redacted)
    redacted = re.sub(
        r"Bearer\s+[A-Za-z0-9_\-\.]+",
        "Bearer [REDACTED_TOKEN]",
        redacted,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"([?&](?:key|api_key|apiKey|access_token|auth|signature)=)[^&\s\"'<>()]+",
        r"\1[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        r"https?://[a-zA-Z0-9.\-_]*\.corp\.goog[^\s\"'<>)]*",
        "[INTERNAL_HOST]",
        redacted,
    )
    redacted = re.sub(
        r"https?://[a-zA-Z0-9.\-_]*\.sandbox\.googleapis\.com[^\s\"'<>)]*",
        "[SANDBOX_ENDPOINT]",
        redacted,
    )
    return redacted


def sanitize_error(err):
    """Sanitizes error strings by redacting secrets, raw HTTP bodies, HTML dumps, and oversized messages."""
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

    err_str = redact_secrets(err_str)
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
    if len(err_str) > MAX_SANITIZED_ERROR_LENGTH:
        err_str = err_str[: MAX_SANITIZED_ERROR_LENGTH - 3] + "..."

    return err_str


def truncate_for_log(text, max_len=MAX_LOGGED_PROMPT_LENGTH):
    """Redacts secrets and truncates long strings for structured logging with char/byte counts."""
    if text is None:
        return ""
    raw_str = str(text)
    total_chars = len(raw_str)
    total_bytes = len(raw_str.encode("utf-8"))
    redacted = redact_secrets(raw_str)
    if len(redacted) <= max_len:
        return redacted
    return (
        f"{redacted[:max_len]}... "
        f"[truncated, total_chars={total_chars}, total_bytes={total_bytes}]"
    )


def acquire_batch_lock(lock_path=None):
    """Acquires a non-blocking OS-level lock to prevent duplicate concurrent batch executions.

    Keeps the lock file descriptor open in module-level `_BATCH_LOCK_FD` for the
    process lifetime so the kernel automatically releases the lock upon termination.
    Returns True if acquired (or on non-POSIX systems without `fcntl`), False if locked.
    """
    global _BATCH_LOCK_FD
    target_lock = lock_path or video_config_mod.BATCH_LOCK_FILE_PATH
    if fcntl is None:
        return True
    if _BATCH_LOCK_FD is not None:
        return True

    parent = os.path.dirname(target_lock)
    if parent:
        os.makedirs(parent, exist_ok=True)

    fd = open(target_lock, "a+", encoding="utf-8")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        logger.info(
            "Another batch instance of generate_video.py is already running (lock=%s). Exiting cleanly.",
            target_lock,
        )
        return False
    except OSError:
        fd.close()
        raise

    _BATCH_LOCK_FD = fd
    logger.info("Acquired single-instance batch lock at %s", target_lock)
    return True


def _extract_remote_file_id(uri):
    """Extracts `<id>` if `uri` matches `FILES_API_BASE_URL` or bare `files/<id>`, else returns None."""
    if not uri or not isinstance(uri, str):
        return None
    candidate = uri.strip()
    bare_match = _BARE_FILE_HANDLE_RE.match(candidate)
    if bare_match:
        return bare_match.group(1)

    parsed_candidate = urllib.parse.urlparse(candidate)
    if parsed_candidate.scheme not in ("http", "https") or not parsed_candidate.netloc:
        return None

    base_parsed = urllib.parse.urlparse(_get_files_api_base_url())
    if parsed_candidate.netloc.lower() != base_parsed.netloc.lower():
        return None

    # Accept both `/files/<id>` and versioned `/v1beta/files/<id>` paths on the configured host
    base_tail = base_parsed.path.rstrip("/") or "/files"
    cand_path = parsed_candidate.path.rstrip("/")
    pattern = re.compile(
        r"^(?:/v[0-9a-z_]+)?" + re.escape(base_tail) + r"/([A-Za-z0-9_\-]+)$"
    )
    path_match = pattern.match(cand_path)
    if path_match:
        return path_match.group(1)
    return None


def is_file_uri(uri):
    """Returns True if `uri` is a configured Files API URI or a bare `files/<id>` resource handle."""
    return _extract_remote_file_id(uri) is not None


def normalize_file_uri(uri):
    """Normalizes a Files API URI or `files/<id>` handle to canonical URL form without query params."""
    if not uri:
        return None
    file_id = _extract_remote_file_id(uri)
    if file_id:
        return f"{_get_files_api_base_url()}/{file_id}"
    return strip_query_params(uri)


def slugify(text):
    """Converts a prompt string into a filesystem-safe slug capped at MAX_SLUG_LENGTH chars."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", (text or "").lower())
    return cleaned.strip("_")[:MAX_SLUG_LENGTH] or "video"


def _normalize_list_arg(value):
    """Normalizes an optional string-or-list media argument into a flat list of non-empty strings."""
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item]
    return [str(value)]


def parse_and_validate_duration(value, has_both_keyframes=False):
    """Parses and validates clip duration (`3s`–`15s`, or `3s`–`10s` for two-frame interpolation)."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"Invalid duration value: '{value}'. Must be an integer.")
    if isinstance(value, (int, float)):
        val = float(value)
    else:
        clean_value = str(value).strip().lower()
        if clean_value in ("none", ""):
            return None
        if clean_value.endswith("s"):
            clean_value = clean_value[:-1]
        try:
            val = float(clean_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid duration value: '{value}'. Must be an integer between "
                f"{MIN_DURATION_SECONDS} and {MAX_DURATION_SECONDS} (e.g., 5, 10, 15)."
            ) from exc

    if not val.is_integer():
        raise ValueError(
            f"Duration must be a whole integer number of seconds, not a float (got {value})."
        )

    val_int = int(val)
    if val_int < MIN_DURATION_SECONDS or val_int > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Duration must be between {MIN_DURATION_SECONDS} (inclusive) and "
            f"{MAX_DURATION_SECONDS} (inclusive) seconds. Got {val_int}."
        )

    if has_both_keyframes and val_int > MAX_KEYFRAME_DURATION_SECONDS:
        raise ValueError(
            "Two-frame keyframe interpolation (--first-frame with --last-frame) "
            f"supports durations between {MIN_DURATION_SECONDS} and "
            f"{MAX_KEYFRAME_DURATION_SECONDS} seconds. Got {val_int}s."
        )

    return f"{val_int}s"


def argparse_duration_type(value):
    """`argparse` converter validating raw duration bounds (`3`–`15` seconds)."""
    if value is None or str(value).strip().lower() in ("none", ""):
        return None
    try:
        return parse_and_validate_duration(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def parse_and_validate_resolution(value):
    """Validates and normalizes video output resolution to one of SUPPORTED_RESOLUTIONS."""
    if value is None:
        return None
    val = str(value).strip().lower()
    if val in ("none", ""):
        return None
    if val in SUPPORTED_RESOLUTIONS:
        return val
    supported_display = ", ".join(SUPPORTED_RESOLUTIONS)
    raise ValueError(
        f"Invalid resolution '{value}'. Supported resolutions for Gemini Omni 1.2 Flash are: {supported_display}."
    )


def argparse_resolution_type(value):
    """`argparse` converter validating video resolution."""
    if value is None or str(value).strip().lower() in ("none", ""):
        return None
    try:
        return parse_and_validate_resolution(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def parse_and_validate_concurrency(value):
    """Validates batch worker concurrency against [1, MAX_BATCH_CONCURRENCY]."""
    max_workers = video_config_mod.MAX_BATCH_CONCURRENCY
    try:
        workers = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Concurrency must be an integer (got '{value}').") from exc
    if workers < 1 or workers > max_workers:
        raise ValueError(
            f"Concurrency must be between 1 and {max_workers} (got {workers})."
        )
    return workers


def argparse_concurrency_type(value):
    """`argparse` converter enforcing bounded parallel batch concurrency."""
    try:
        return parse_and_validate_concurrency(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def validate_video_reference_constraints(
    ref_videos,
    video_paths,
    extend_video=None,
    previous_interaction_id=None,
    task=None,
    duration=None,
    ref_images=None,
):
    """Validates Omni 1.2 Flash reference media constraints before uploading or calling the API."""
    if ref_images and len(ref_images) > MAX_REF_IMAGES:
        logger.warning(
            "%d reference images provided; up to %d reference images (--image) are recommended.",
            len(ref_images),
            MAX_REF_IMAGES,
        )

    if not ref_videos:
        return

    if (
        video_paths
        or extend_video
        or previous_interaction_id
        or task in ("edit", "extend")
    ):
        raise ValueError(
            "Reference videos (--video-reference) are supported only when generating a new video "
            "and cannot be combined with video editing (--video / task='edit'), video extension "
            "(--extend / task='extend'), or multi-turn editing/extension (--previous-interaction-id). "
            "Reference images (--image) ARE supported for editing and extension—use --image instead."
        )

    if duration == f"{MAX_DURATION_SECONDS}s" and len(ref_videos) > MAX_15S_REF_VIDEOS:
        raise ValueError(
            f"{MAX_DURATION_SECONDS}-second video generations support at most "
            f"{MAX_15S_REF_VIDEOS} reference video (--video-reference); got {len(ref_videos)}. "
            f"Reduce --duration to {MAX_DURATION_SECONDS - 1}s or fewer, pass a single reference video, "
            f"or use reference images (--image, up to {MAX_REF_IMAGES} supported on {MAX_DURATION_SECONDS}s clips)."
        )

    if len(ref_videos) > MAX_RECOMMENDED_REF_VIDEOS:
        logger.warning(
            "%d reference videos provided; up to %d short (~3s) reference videos are recommended.",
            len(ref_videos),
            MAX_RECOMMENDED_REF_VIDEOS,
        )


def build_natural_language_prompt(
    prompt,
    first_frame=None,
    last_frame=None,
    extend_video=None,
):
    """Builds a natural-language media-binding prompt without deprecated `<FIRST_FRAME>` / `<IMAGE_REF_*>` tags."""
    base_prompt = (prompt or "").strip()
    lower_prompt = base_prompt.lower()

    if extend_video:
        if not any(
            token in lower_prompt
            for token in ("extend", "continues", "continuation", "keep going")
        ):
            return f"Extend this video. {base_prompt}"
        return base_prompt

    if first_frame and last_frame:
        if first_frame == last_frame:
            if not any(
                token in lower_prompt
                for token in ("starting frame", "first frame", "final frame", "loop")
            ):
                return f"Use this image as both the starting frame and the final frame. {base_prompt}"
            return base_prompt
        if not any(
            token in lower_prompt
            for token in (
                "starting frame",
                "first frame",
                "first image",
                "final frame",
                "last frame",
            )
        ):
            return (
                "Use the first image as the starting frame and the second image as the final frame. "
                f"{base_prompt}"
            )
        return base_prompt

    if first_frame:
        if not any(
            token in lower_prompt
            for token in ("starting frame", "first frame", "this image")
        ):
            return f"Use this image as the starting frame. {base_prompt}"

    return base_prompt


def _guess_local_mime_type(asset_path, fallback_mime):
    """Guesses a local asset MIME type from its extension, falling back to `fallback_mime`."""
    guessed, _ = mimetypes.guess_type(asset_path)
    return guessed or fallback_mime


def _get_per_asset_lock(cache_key):
    """Returns a dedicated `threading.Lock` for `cache_key` to coalesce concurrent identical uploads."""
    with _ASSET_UPLOAD_LOCK:
        lock = _ASSET_KEY_LOCKS.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _ASSET_KEY_LOCKS[cache_key] = lock
        return lock


def _call_upload_file(upload_path, allow_interactive):
    """Calls `upload_file` passing `interactive=allow_interactive` when supported by its signature."""
    try:
        sig = inspect.signature(upload_file)
        if "interactive" in sig.parameters:
            return upload_file(upload_path, interactive=allow_interactive)
    except (TypeError, ValueError):
        pass
    return upload_file(upload_path)


def _call_wait_for_active(file_name, timeout_s):
    """Calls `wait_for_active` forwarding `max_timeout=timeout_s` when supported by its signature."""
    try:
        sig = inspect.signature(wait_for_active)
        if "max_timeout" in sig.parameters:
            return wait_for_active(file_name, max_timeout=timeout_s)
    except (TypeError, ValueError):
        pass
    return wait_for_active(file_name)


def resolve_or_upload_asset(
    asset_path,
    mime_type,
    strip_audio=False,
    dry_run=False,
    timeout_s=DEFAULT_HTTP_TIMEOUT_SECONDS,
    allow_interactive=None,
):
    """Resolves a Files API URI or uploads a local media file with per-asset thread coalescing.

    Checks existing local paths before treating non-HTTP `files/...` strings as remote handles.
    When `dry_run=True`, verifies local file existence and returns a deterministic
    placeholder URI without performing `ffmpeg` mutation or Files API network calls.
    """
    if not asset_path:
        return None, None

    asset_str = str(asset_path).strip()
    is_http_url = asset_str.lower().startswith(("http://", "https://"))

    # Local filesystem paths take precedence over bare `files/...` strings so local `files/foo.png` works
    if not is_http_url and os.path.exists(asset_str):
        is_local_file = True
    elif is_file_uri(asset_str):
        if strip_audio:
            raise ValueError(
                "Error: --strip-audio cannot be applied to an existing remote File API URI. "
                "Please provide a local video file so audio can be stripped before upload."
            )
        normalized = normalize_file_uri(asset_str)
        logger.info("Resolved existing Files API URI: %s", strip_query_params(normalized))
        return normalized, mime_type
    elif not is_http_url:
        raise FileNotFoundError(
            f"Asset path '{asset_str}' is neither a valid File API URI nor an existing local file."
        )
    else:
        raise FileNotFoundError(
            f"Remote URI '{strip_query_params(asset_str)}' does not match configured Files API base '{_get_files_api_base_url()}'."
        )

    if not is_local_file:  # pragma: no cover - defensive guard
        raise FileNotFoundError(f"Asset path '{asset_str}' not found.")

    resolved_local = os.path.abspath(asset_str)
    local_mime = _guess_local_mime_type(resolved_local, mime_type)

    if dry_run:
        placeholder_slug = slugify(os.path.basename(resolved_local))
        dry_uri = f"{_get_files_api_base_url()}/dry_run_{placeholder_slug}"
        logger.info(
            "[DRY-RUN] Verified local asset '%s' (mime=%s, strip_audio=%s) -> %s",
            resolved_local,
            local_mime,
            strip_audio,
            dry_uri,
        )
        return dry_uri, local_mime

    if not get_api_key():
        raise RuntimeError(
            f"Error: {GEMINI_API_KEY_ENV} environment variable is not set."
        )

    if allow_interactive is None:
        allow_interactive = bool(
            sys.stdin
            and sys.stdin.isatty()
            and threading.current_thread() is threading.main_thread()
        )

    cache_key = (resolved_local, bool(strip_audio))
    key_lock = _get_per_asset_lock(cache_key)

    with key_lock:
        with _ASSET_UPLOAD_LOCK:
            if cache_key in _ASSET_CACHE:
                cached_uri, cached_mime = _ASSET_CACHE[cache_key]
                logger.info(
                    "Reusing cached uploaded asset for '%s': %s",
                    resolved_local,
                    strip_query_params(cached_uri),
                )
                return cached_uri, cached_mime

        upload_path = resolved_local
        temp_stripped_path = None

        try:
            if strip_audio:
                logger.info(
                    "Stripping audio stream from local video '%s' before upload...",
                    resolved_local,
                )
                ffmpeg_bin = shutil.which("ffmpeg")
                if not ffmpeg_bin:
                    raise RuntimeError(
                        "Error: ffmpeg is not installed or not found in system PATH. "
                        "ffmpeg is required to strip audio from local videos when --strip-audio is specified."
                    )

                _, ext = os.path.splitext(os.path.basename(resolved_local))
                tmp_fd, temp_stripped_path = tempfile.mkstemp(
                    prefix=TEMP_STRIPPED_PREFIX,
                    suffix=ext or ".mp4",
                    dir=tempfile.gettempdir(),
                )
                os.close(tmp_fd)

                cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-i",
                    resolved_local,
                    "-c:v",
                    "copy",
                    "-an",
                    temp_stripped_path,
                ]
                try:
                    proc = subprocess.run(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                        timeout=FFMPEG_STRIP_AUDIO_TIMEOUT_SECONDS,
                    )
                except FileNotFoundError as exc:
                    raise RuntimeError(
                        "Error: ffmpeg binary could not be executed when stripping audio."
                    ) from exc
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError(
                        f"ffmpeg timed out after {FFMPEG_STRIP_AUDIO_TIMEOUT_SECONDS}s while stripping audio from '{resolved_local}'."
                    ) from exc

                if proc.returncode != 0:
                    err_msg = (
                        sanitize_error(proc.stderr.strip())
                        if proc.stderr
                        else "Unknown ffmpeg error"
                    )
                    raise RuntimeError(
                        f"ffmpeg failed to strip audio from '{resolved_local}': {err_msg}"
                    )

                upload_path = temp_stripped_path

            logger.info("Uploading local asset '%s' via Files API...", upload_path)
            file_meta = _call_upload_file(
                upload_path, allow_interactive=allow_interactive
            )
            file_name = file_meta.get("name")
            file_meta = _call_wait_for_active(file_name, timeout_s=timeout_s)
            normalized = normalize_file_uri(file_meta.get("uri"))
            returned_mime = (
                file_meta.get("mimeType") or file_meta.get("mime_type") or local_mime
            )

            with _ASSET_UPLOAD_LOCK:
                _ASSET_CACHE[cache_key] = (normalized, returned_mime)

            return normalized, returned_mime
        finally:
            if temp_stripped_path and os.path.exists(temp_stripped_path):
                try:
                    os.remove(temp_stripped_path)
                    logger.info(
                        "Removed temporary audio-stripped video file: %s",
                        temp_stripped_path,
                    )
                except OSError as exc:
                    logger.warning(
                        "Failed to remove temporary file %s: %s",
                        temp_stripped_path,
                        sanitize_error(exc),
                    )


def download_video_file(file_or_uri, output_path, client=None):
    """Streams a generated video file directly to `output_path` via `client.files.download`."""
    if not file_or_uri:
        raise ValueError("Download error: file reference or URI is required.")

    if not get_api_key():
        raise RuntimeError(
            f"Error: {GEMINI_API_KEY_ENV} environment variable is not set."
        )

    if client is None:
        client = genai.Client(
            http_options=types.HttpOptions(timeout=DEFAULT_HTTP_TIMEOUT_SECONDS * 1000)
        )

    display_uri = getattr(file_or_uri, "uri", str(file_or_uri))
    clean_uri = strip_query_params(display_uri)
    logger.info("Downloading generated video from %s to %s", clean_uri, output_path)
    print(f"Downloading video from {clean_uri} to {output_path} via SDK...")
    try:
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        download_target = getattr(file_or_uri, "uri", file_or_uri)
        try:
            result = client.files.download(
                file=download_target, destination=output_path
            )
        except TypeError:
            # Fallback for older SDKs or test mocks without `destination` keyword
            result = client.files.download(file=download_target)

        if isinstance(result, (bytes, bytearray)) and (
            not os.path.exists(output_path) or os.path.getsize(output_path) == 0
        ):
            with open(output_path, "wb") as out_f:
                out_f.write(result)

        written_bytes = (
            os.path.getsize(output_path) if os.path.exists(output_path) else 0
        )
        logger.info(
            "Saved generated video (%d bytes) to %s", written_bytes, output_path
        )
        print(f"Video successfully saved to: {output_path}")
    except Exception as exc:
        raise RuntimeError(
            f"Error downloading video file via SDK: {sanitize_error(exc)}"
        ) from exc


def generate_video(
    prompt,
    model=DEFAULT_MODEL,
    aspect_ratio=DEFAULT_ASPECT_RATIO,
    duration=None,
    resolution=None,
    first_frame=None,
    last_frame=None,
    image_path=None,
    image_reference=None,
    video_path=None,
    extend_video=None,
    video_reference=None,
    task=None,
    output_path=DEFAULT_OUTPUT_PATH,
    strip_audio=False,
    previous_interaction_id=None,
    timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
    dry_run=False,
    allow_interactive=None,
):
    """Creates a video generation/editing/extension interaction and downloads the output MP4.

    When `dry_run=True`, validates all Omni 1.2 Flash parameters and local asset paths,
    logs the exact `interactions.create` payload, and returns `create_kwargs` without
    making network requests.
    """
    if not prompt or not str(prompt).strip():
        raise ValueError("A non-empty text prompt is required.")

    resolved_model = DEFAULT_MODEL if model is None else str(model).strip()
    if not resolved_model:
        raise ValueError("Model ID must not be empty.")

    resolved_aspect_ratio = (
        DEFAULT_ASPECT_RATIO if aspect_ratio is None else str(aspect_ratio).strip()
    )
    if resolved_aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(
            f"Invalid aspect_ratio '{aspect_ratio}'. Supported values: {', '.join(SUPPORTED_ASPECT_RATIOS)}."
        )

    if last_frame and not first_frame:
        raise ValueError(
            "--last-frame must be used with --first-frame "
            "(the model requires a starting frame when specifying a final frame)."
        )

    resolved_task = None if task is None else str(task).strip()
    if resolved_task == "":
        resolved_task = None
    if resolved_task and resolved_task not in SUPPORTED_TASKS:
        raise ValueError(
            f"Invalid task '{task}'. Supported values: {', '.join(SUPPORTED_TASKS)}."
        )

    timeout_s = int(timeout) if timeout is not None else DEFAULT_HTTP_TIMEOUT_SECONDS
    if timeout_s <= 0:
        raise ValueError(f"Timeout must be greater than 0 seconds (got {timeout}).")

    has_both_keyframes = bool(first_frame and last_frame)
    validated_duration = parse_and_validate_duration(
        duration, has_both_keyframes=has_both_keyframes
    )
    validated_resolution = parse_and_validate_resolution(resolution)

    ref_images = _normalize_list_arg(image_path) + _normalize_list_arg(image_reference)
    source_videos = _normalize_list_arg(video_path)
    ref_videos = _normalize_list_arg(video_reference)

    validate_video_reference_constraints(
        ref_videos=ref_videos,
        video_paths=source_videos,
        extend_video=extend_video,
        previous_interaction_id=previous_interaction_id,
        task=resolved_task,
        duration=validated_duration,
        ref_images=ref_images,
    )

    if not dry_run and not get_api_key():
        raise RuntimeError(
            f"Error: {GEMINI_API_KEY_ENV} environment variable is not set."
        )

    logger.info(
        "Preparing video generation request (model=%s, aspect_ratio=%s, duration=%s, "
        "resolution=%s, task=%s, first_frame=%s, last_frame=%s, ref_images=%d, "
        "source_videos=%d, extend=%s, ref_videos=%d, dry_run=%s)",
        resolved_model,
        resolved_aspect_ratio,
        validated_duration or "default",
        validated_resolution or "default",
        resolved_task or "auto",
        bool(first_frame),
        bool(last_frame),
        len(ref_images),
        len(source_videos),
        bool(extend_video),
        len(ref_videos),
        dry_run,
    )

    input_parts = []

    # 1. Starting frame image
    f1_uri = None
    f1_mime = None
    if first_frame:
        f1_uri, f1_mime = resolve_or_upload_asset(
            first_frame,
            "image/png",
            dry_run=dry_run,
            timeout_s=timeout_s,
            allow_interactive=allow_interactive,
        )
        input_parts.append({"type": "image", "uri": f1_uri, "mime_type": f1_mime})

    # 2. Final frame image (reuses starting frame URI for seamless loops)
    if last_frame:
        if last_frame == first_frame and f1_uri:
            input_parts.append({"type": "image", "uri": f1_uri, "mime_type": f1_mime})
        else:
            f2_uri, f2_mime = resolve_or_upload_asset(
                last_frame,
                "image/png",
                dry_run=dry_run,
                timeout_s=timeout_s,
                allow_interactive=allow_interactive,
            )
            input_parts.append({"type": "image", "uri": f2_uri, "mime_type": f2_mime})

    # 3. Reference images (R2V or image-guided extension/editing)
    for img in ref_images:
        img_uri, img_mime = resolve_or_upload_asset(
            img,
            "image/png",
            dry_run=dry_run,
            timeout_s=timeout_s,
            allow_interactive=allow_interactive,
        )
        input_parts.append({"type": "image", "uri": img_uri, "mime_type": img_mime})

    # 4. Source video(s) for extension or editing
    if extend_video:
        ext_uri, ext_mime = resolve_or_upload_asset(
            extend_video,
            "video/mp4",
            strip_audio=strip_audio,
            dry_run=dry_run,
            timeout_s=timeout_s,
            allow_interactive=allow_interactive,
        )
        input_parts.append({"type": "video", "uri": ext_uri, "mime_type": ext_mime})

    for vid in source_videos:
        vid_uri, vid_mime = resolve_or_upload_asset(
            vid,
            "video/mp4",
            strip_audio=strip_audio,
            dry_run=dry_run,
            timeout_s=timeout_s,
            allow_interactive=allow_interactive,
        )
        input_parts.append({"type": "video", "uri": vid_uri, "mime_type": vid_mime})

    # 5. Reference videos (new video generation only; unlike --image, not used for edit/extend)
    for ref_vid in ref_videos:
        rv_uri, rv_mime = resolve_or_upload_asset(
            ref_vid,
            "video/mp4",
            strip_audio=strip_audio,
            dry_run=dry_run,
            timeout_s=timeout_s,
            allow_interactive=allow_interactive,
        )
        input_parts.append({"type": "video", "uri": rv_uri, "mime_type": rv_mime})

    # 6. Natural-language prompt binding (no deprecated role tags)
    prompt_text = build_natural_language_prompt(
        prompt=prompt,
        first_frame=first_frame,
        last_frame=last_frame,
        extend_video=extend_video,
    )
    input_parts.append({"type": "text", "text": prompt_text})

    video_config = {
        "type": "video",
        "delivery": "uri",
    }
    if resolved_task != "extend":
        video_config["aspect_ratio"] = resolved_aspect_ratio
    if validated_duration:
        video_config["duration"] = validated_duration
    if validated_resolution:
        video_config["resolution"] = validated_resolution

    generation_config = None
    if resolved_task and not previous_interaction_id:
        generation_config = {"video_config": {"task": resolved_task}}

    create_kwargs = {
        "model": resolved_model,
        "input": input_parts,
        "response_format": video_config,
    }
    if generation_config:
        create_kwargs["generation_config"] = generation_config
    if previous_interaction_id:
        create_kwargs["previous_interaction_id"] = previous_interaction_id

    media_parts_summary = [
        {"type": p["type"], "uri": strip_query_params(p.get("uri", ""))}
        for p in input_parts
        if p.get("type") != "text"
    ]
    logger.info(
        "LLM Interaction Request -> model=%s response_format=%s generation_config=%s "
        "previous_interaction_id=%s media_inputs=%s prompt=%r",
        resolved_model,
        video_config,
        generation_config,
        previous_interaction_id,
        media_parts_summary,
        truncate_for_log(prompt_text),
    )

    if dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "output_path": output_path,
                    "timeout_seconds": timeout_s,
                    "request": create_kwargs,
                },
                indent=2,
            )
        )
        return create_kwargs

    res_display = video_config.get("resolution", "default (720p)")
    print(
        f"\nSending generation request using official google-genai SDK and model '{resolved_model}'..."
    )
    print(
        f"Prompt: '{truncate_for_log(prompt_text)}' | "
        f"Aspect Ratio: {video_config.get('aspect_ratio', 'inherited')} | "
        f"Resolution: {res_display} | "
        f"Duration: {validated_duration or 'default (10s)'}"
    )
    if res_display == "4k":
        print(
            "Note: 4K video generation selected. Processing high-resolution video may take longer to complete."
        )
    if resolved_task:
        print(f"Task Mode: {resolved_task}")

    client = genai.Client(http_options=types.HttpOptions(timeout=timeout_s * 1000))
    try:
        interaction = client.interactions.create(**create_kwargs)
    except errors.APIError as exc:
        raise RuntimeError(
            f"API Error generating video via SDK: {sanitize_error(exc)}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Error generating video via SDK: {sanitize_error(exc)}"
        ) from exc

    interaction_id = getattr(interaction, "id", None)
    interaction_status = getattr(interaction, "status", None)
    interaction_usage = getattr(interaction, "usage", None)
    output_video = getattr(interaction, "output_video", None)
    video_uri = getattr(output_video, "uri", None) if output_video else None

    logger.info(
        "LLM Interaction Response <- model=%s interaction_id=%s status=%s usage=%s has_video=%s video_uri=%s",
        resolved_model,
        interaction_id,
        interaction_status,
        redact_secrets(interaction_usage) if interaction_usage is not None else None,
        bool(video_uri),
        strip_query_params(video_uri) if video_uri else None,
    )

    print(
        f"Generation complete for '{truncate_for_log(prompt, SHORT_LOG_PROMPT_LENGTH)}'! Processing response..."
    )
    if interaction_id:
        print(f"Interaction ID: {interaction_id}")

    if not output_video or not video_uri:
        err_msg = (
            f"No video content found in response for '{truncate_for_log(prompt, SHORT_LOG_PROMPT_LENGTH)}'."
        )
        if source_videos or extend_video or ref_videos:
            err_msg += (
                "\nWARNING: IMPORTANT REGIONAL RESTRICTION: Uploading videos to use for video edits, "
                "extensions, or references is not available in the EEA, Switzerland, United Kingdom, "
                "and some US states."
            )
        raise RuntimeError(err_msg)

    print(f"Generated video URI: {strip_query_params(video_uri)}")
    download_video_file(output_video, output_path, client=client)
    return create_kwargs


def assign_unique_batch_outputs(jobs):
    """Assigns collision-free `output` paths across batch jobs so worker threads never overwrite each other."""
    seen_abs_paths = set()
    prepared = []

    for idx, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            prepared.append(job)
            continue

        job_copy = dict(job)
        prompt = job_copy.get("prompt")
        if not prompt or not str(prompt).strip():
            prepared.append(job_copy)
            continue

        raw_out = job_copy.get("output")
        if raw_out and str(raw_out).strip():
            candidate = str(raw_out).strip()
        else:
            candidate = (
                f"{DEFAULT_BATCH_OUTPUT_DIR}/output_{idx:03d}_{slugify(prompt)}.mp4"
            )

        abs_candidate = os.path.abspath(candidate)
        if abs_candidate in seen_abs_paths:
            stem, ext = os.path.splitext(candidate)
            ext = ext or ".mp4"
            suffix_num = idx
            while True:
                disambiguated = f"{stem}_job{suffix_num:03d}{ext}"
                abs_disambiguated = os.path.abspath(disambiguated)
                if abs_disambiguated not in seen_abs_paths:
                    logger.warning(
                        "Duplicate batch output path '%s' detected on job #%d; writing to '%s' instead.",
                        candidate,
                        idx,
                        disambiguated,
                    )
                    candidate = disambiguated
                    abs_candidate = abs_disambiguated
                    break
                suffix_num += 1

        seen_abs_paths.add(abs_candidate)
        job_copy["output"] = candidate
        prepared.append(job_copy)

    return prepared


def run_job(job, dry_run=False, job_index=1):
    """Executes a single generation job inside a bounded thread pool, returning a status dict."""
    if not isinstance(job, dict):
        return {
            "job": {"prompt": str(job)},
            "status": "FAILED",
            "error": "Job entry must be a JSON object",
        }

    prompt = job.get("prompt")
    if not prompt or not str(prompt).strip():
        logger.warning("Skipping batch job #%d with empty prompt.", job_index)
        return {"job": job, "status": "SKIPPED", "error": "Empty prompt"}

    first_frame = job.get("first_frame")
    last_frame = job.get("last_frame")
    aspect_ratio = (
        DEFAULT_ASPECT_RATIO
        if "aspect_ratio" not in job or job.get("aspect_ratio") is None
        else job.get("aspect_ratio")
    )
    duration = job.get("duration")
    resolution = job.get("resolution")
    image_path = job.get("image") or job.get("image_reference") or job.get("ref_image")
    video_path = job.get("video")
    extend_video = job.get("extend") or job.get("extend_video")
    video_reference = (
        job.get("video_reference") or job.get("ref_video") or job.get("video_ref")
    )
    task = job.get("task")
    raw_output = job.get("output")
    output_path = (
        str(raw_output).strip()
        if raw_output and str(raw_output).strip()
        else f"{DEFAULT_BATCH_OUTPUT_DIR}/output_{job_index:03d}_{slugify(prompt)}.mp4"
    )
    model = (
        DEFAULT_MODEL
        if "model" not in job or job.get("model") is None
        else job.get("model")
    )
    strip_audio = bool(job.get("strip_audio", False))
    previous_interaction_id = job.get("previous_interaction_id")
    timeout = (
        DEFAULT_HTTP_TIMEOUT_SECONDS
        if job.get("timeout") is None
        else job.get("timeout")
    )
    job_dry_run = bool(dry_run or job.get("dry_run", False))

    print(
        f"[Parallel] Dispatching job #{job_index}: "
        f"'{truncate_for_log(prompt, BATCH_LOG_PROMPT_LENGTH)}' (Output: {output_path})"
    )
    try:
        generate_video(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            first_frame=first_frame,
            last_frame=last_frame,
            image_path=image_path,
            video_path=video_path,
            extend_video=extend_video,
            video_reference=video_reference,
            task=task,
            output_path=output_path,
            strip_audio=strip_audio,
            previous_interaction_id=previous_interaction_id,
            timeout=timeout,
            dry_run=job_dry_run,
            allow_interactive=False,
        )
        return {"job": job, "status": "SUCCESS", "output_path": output_path}
    except Exception as exc:
        cleaned_err = sanitize_error(exc)
        logger.error(
            "Batch job #%d failed for '%s': %s",
            job_index,
            truncate_for_log(prompt, BATCH_LOG_PROMPT_LENGTH),
            cleaned_err,
        )
        print(
            f"[Parallel] Failed: '{truncate_for_log(prompt, BATCH_LOG_PROMPT_LENGTH)}' - Error: {cleaned_err}",
            file=sys.stderr,
        )
        return {"job": job, "status": "FAILED", "error": cleaned_err}


class SanitizedArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that sanitizes error messages to prevent accidental secret leaks."""

    def error(self, message):
        """Prints usage and exits with code 2 after redacting sensitive tokens from `message`."""
        sanitized_msg = sanitize_error(message)
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {sanitized_msg}\n")


def build_arg_parser():
    """Builds and returns the CLI argument parser for `generate_video.py`."""
    parser = SanitizedArgumentParser(
        description=(
            f"Generate, extend, and edit videos using Gemini Omni 1.2 Flash ({DEFAULT_MODEL}) "
            "via the official google-genai SDK (supports --dry-run and parallel batch execution)."
        )
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Text prompt / instruction for a single video generation",
    )
    parser.add_argument(
        "--first-frame",
        "-f",
        help="Local image path or File API URI for the starting frame",
    )
    parser.add_argument(
        "--last-frame",
        "-l",
        help="Local image path or File API URI for the final frame (must be used with --first-frame; 3s–10s max)",
    )
    parser.add_argument(
        "--image",
        "--image-reference",
        "--ref-image",
        "-i",
        action="append",
        dest="image",
        help=(
            "Optional local image path or File API URI for reference-guided generation (R2V), "
            f"video editing, or video extension (repeatable, up to {MAX_REF_IMAGES} images "
            f"including {MAX_DURATION_SECONDS}s clips)"
        ),
    )
    parser.add_argument(
        "--video",
        "-v",
        action="append",
        help="Optional local video path or File API URI for video editing (repeatable, source <= 10s)",
    )
    parser.add_argument(
        "--extend",
        "-e",
        help=(
            f"Optional local video path or File API URI to extend "
            f"({MIN_DURATION_SECONDS}s–{MAX_DURATION_SECONDS}s per turn, up to {MAX_TOTAL_EXTENDED_SECONDS}s total)"
        ),
    )
    parser.add_argument(
        "--video-reference",
        "--ref-video",
        "-vr",
        action="append",
        dest="video_reference",
        help=(
            "Optional local video path or File API URI to guide new video generation "
            f"(repeatable; ~3s ideal; up to {MAX_RECOMMENDED_REF_VIDEOS} for "
            f"<={MAX_DURATION_SECONDS - 1}s clips, max {MAX_15S_REF_VIDEOS} for "
            f"{MAX_DURATION_SECONDS}s clips; new video generation only — unlike --image, "
            "not supported for editing or extension)"
        ),
    )
    parser.add_argument(
        "--task",
        choices=list(SUPPORTED_TASKS),
        default=None,
        help=(
            "Optional fallback video task mode (leave unset by default so natural-language prompting "
            "and reference-image edits/extensions work without strict task media-count gates)"
        ),
    )
    parser.add_argument(
        "--aspect-ratio",
        default=DEFAULT_ASPECT_RATIO,
        choices=list(SUPPORTED_ASPECT_RATIOS),
        help=f"Aspect ratio (default: {DEFAULT_ASPECT_RATIO}; omitted automatically if task='extend')",
    )
    parser.add_argument(
        "--duration",
        type=argparse_duration_type,
        default=None,
        help=(
            f"Video duration as an integer between {MIN_DURATION_SECONDS} and {MAX_DURATION_SECONDS} seconds "
            f"(3–{MAX_KEYFRAME_DURATION_SECONDS}s when combining --first-frame and --last-frame). "
            "Default: None (10s model default)"
        ),
    )
    parser.add_argument(
        "--resolution",
        "-res",
        type=argparse_resolution_type,
        default=None,
        help="Video output resolution: 360p, 720p (default), 1080p, or 4k",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini Omni Flash video model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        "-o",
        help=f"Local output file path for single generation (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--strip-audio",
        "-a",
        action="store_true",
        help="Strip audio stream from local input video(s) before upload so Omni Flash regenerates audio from scratch",
    )
    parser.add_argument(
        "--previous-interaction-id",
        help="Optional Interaction ID of a previous generation for multi-turn editing or extending",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_HTTP_TIMEOUT_SECONDS,
        help=f"Per-request HTTP timeout in seconds (default: {DEFAULT_HTTP_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the Interactions API request payload without uploading files or calling the API",
    )
    parser.add_argument(
        "--batch",
        help="Path to a JSON file containing an array of generation job objects",
    )
    parser.add_argument(
        "--prompts-file",
        help="Path to a text file containing one prompt per line to execute in parallel",
    )
    parser.add_argument(
        "--concurrency",
        type=argparse_concurrency_type,
        default=DEFAULT_BATCH_CONCURRENCY,
        help=f"Maximum number of concurrent batch workers (1–{MAX_BATCH_CONCURRENCY}, default: {DEFAULT_BATCH_CONCURRENCY})",
    )
    return parser


def main(argv=None):
    """CLI entrypoint for single-clip and parallel-batch video generation."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    active_modes = sum(
        bool(mode_val) for mode_val in (args.prompt, args.batch, args.prompts_file)
    )
    if active_modes > 1:
        parser.error(
            "Specify only one execution mode: positional 'prompt', '--batch', or '--prompts-file'."
        )

    exec_mode = (
        "batch_json"
        if args.batch
        else ("prompts_file" if args.prompts_file else "single")
    )
    logger.info(
        "CLI main invoked (mode=%s, model=%s, duration=%s, resolution=%s, aspect_ratio=%s, "
        "task=%s, concurrency=%d, dry_run=%s)",
        exec_mode,
        redact_secrets(args.model),
        args.duration or "default",
        args.resolution or "default",
        args.aspect_ratio,
        args.task or "auto",
        args.concurrency,
        args.dry_run,
    )

    if args.last_frame and not args.first_frame:
        parser.error(
            "--last-frame must be used with --first-frame "
            "(the model requires a starting frame when specifying a final frame)."
        )

    # 1. Batch JSON mode
    if args.batch:
        try:
            if not acquire_batch_lock():
                return 0
        except OSError as exc:
            logger.error(
                "Failed to acquire single-instance batch lock: %s", sanitize_error(exc)
            )
            print(
                f"Error: Failed to acquire batch lock: {sanitize_error(exc)}",
                file=sys.stderr,
            )
            return 1

        if not os.path.exists(args.batch):
            print(f"Error: Batch JSON file '{args.batch}' not found.", file=sys.stderr)
            return 1
        try:
            with open(args.batch, "r", encoding="utf-8") as batch_f:
                jobs = json.load(batch_f)
            if not isinstance(jobs, list):
                print(
                    "Error: Batch JSON file must contain a list/array of job objects.",
                    file=sys.stderr,
                )
                return 1
        except Exception as exc:
            print(f"Error parsing Batch JSON: {sanitize_error(exc)}", file=sys.stderr)
            return 1

        requires_live_api = any(
            isinstance(j, dict)
            and bool((j.get("prompt") or "").strip())
            and not (args.dry_run or bool(j.get("dry_run", False)))
            for j in jobs
        )
        if requires_live_api and not get_api_key():
            print(
                f"Error: {GEMINI_API_KEY_ENV} environment variable is not set.",
                file=sys.stderr,
            )
            return 1

        logger.info(
            "Loaded %d batch jobs from %s (concurrency=%d, dry_run=%s)",
            len(jobs),
            args.batch,
            args.concurrency,
            args.dry_run,
        )
        print(
            f"Loaded {len(jobs)} jobs from batch JSON. Running with concurrency={args.concurrency}..."
        )

    # 2. Prompts text-file mode
    elif args.prompts_file:
        try:
            if not acquire_batch_lock():
                return 0
        except OSError as exc:
            logger.error(
                "Failed to acquire single-instance batch lock: %s", sanitize_error(exc)
            )
            print(
                f"Error: Failed to acquire batch lock: {sanitize_error(exc)}",
                file=sys.stderr,
            )
            return 1

        if not os.path.exists(args.prompts_file):
            print(
                f"Error: Prompts file '{args.prompts_file}' not found.",
                file=sys.stderr,
            )
            return 1

        if not args.dry_run and not get_api_key():
            print(
                f"Error: {GEMINI_API_KEY_ENV} environment variable is not set.",
                file=sys.stderr,
            )
            return 1

        jobs = []
        with open(args.prompts_file, "r", encoding="utf-8") as prompts_f:
            for raw_line in prompts_f:
                line = raw_line.strip()
                if line and not line.startswith("#"):
                    jobs.append(
                        {
                            "prompt": line,
                            "aspect_ratio": args.aspect_ratio,
                            "duration": args.duration,
                            "resolution": args.resolution,
                            "first_frame": args.first_frame,
                            "last_frame": args.last_frame,
                            "image": args.image,
                            "video": args.video,
                            "extend": args.extend,
                            "video_reference": args.video_reference,
                            "task": args.task,
                            "model": args.model,
                            "strip_audio": args.strip_audio,
                            "previous_interaction_id": args.previous_interaction_id,
                            "timeout": args.timeout,
                            "dry_run": args.dry_run,
                        }
                    )
        logger.info(
            "Loaded %d prompts from %s (concurrency=%d, dry_run=%s)",
            len(jobs),
            args.prompts_file,
            args.concurrency,
            args.dry_run,
        )
        print(
            f"Loaded {len(jobs)} prompts from text file. Running with concurrency={args.concurrency}..."
        )

    # 3. Single generation mode
    else:
        if not args.prompt:
            parser.print_help()
            return 1

        if not args.dry_run and not get_api_key():
            print(
                f"Error: {GEMINI_API_KEY_ENV} environment variable is not set.",
                file=sys.stderr,
            )
            return 1

        output_path = args.output if args.output else DEFAULT_OUTPUT_PATH
        try:
            generate_video(
                prompt=args.prompt,
                model=args.model,
                aspect_ratio=args.aspect_ratio,
                duration=args.duration,
                resolution=args.resolution,
                first_frame=args.first_frame,
                last_frame=args.last_frame,
                image_path=args.image,
                video_path=args.video,
                extend_video=args.extend,
                video_reference=args.video_reference,
                task=args.task,
                output_path=output_path,
                strip_audio=args.strip_audio,
                previous_interaction_id=args.previous_interaction_id,
                timeout=args.timeout,
                dry_run=args.dry_run,
            )
            return 0
        except Exception as exc:
            print(f"Error: Generation failed: {sanitize_error(exc)}", file=sys.stderr)
            return 1

    if not jobs:
        print("Warning: No valid jobs found to execute.")
        return 0

    disambiguated_jobs = assign_unique_batch_outputs(jobs)

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(run_job, job, args.dry_run, idx): idx
            for idx, job in enumerate(disambiguated_jobs, start=1)
        }
        for future in as_completed(futures):
            results.append((futures[future], future.result()))

    results.sort(key=lambda pair: pair[0])
    ordered_results = [pair[1] for pair in results]

    print("\n" + "=" * 50)
    print("BATCH PARALLEL EXECUTION SUMMARY")
    print("=" * 50)
    success_count = sum(1 for r in ordered_results if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in ordered_results if r["status"] == "FAILED")
    skipped_count = sum(1 for r in ordered_results if r["status"] == "SKIPPED")

    print(
        f"Total: {len(ordered_results)} | Success: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}\n"
    )
    for r in ordered_results:
        status_str = r["status"]
        job_prompt = (
            r["job"].get("prompt")
            if isinstance(r.get("job"), dict)
            else str(r.get("job"))
        )
        if status_str == "SUCCESS":
            print(f"  [{status_str}] '{job_prompt}' -> {r['output_path']}")
        else:
            print(f"  [{status_str}] '{job_prompt}' -> Error: {r.get('error')}")
    print("=" * 50)

    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
