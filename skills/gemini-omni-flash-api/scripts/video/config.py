#!/usr/bin/env python3
"""Centralized configuration constants for the Gemini Omni Flash video & upload CLIs.

Groups model identifiers, API environment variables, duration and reference limits,
supported resolutions/aspect ratios/tasks, subprocess/HTTP/polling timeouts, file-size
thresholds, and batch execution lock/concurrency bounds in a single configuration module
with environment variable overrides where appropriate.
"""

import os
import tempfile


def _env_str(name, default):
    """Reads a non-empty string environment variable, falling back to `default` when unset or blank."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip()


def _env_int(name, default):
    """Reads an integer environment variable, falling back to `default` when unset or blank."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw.strip())


# Model & API configuration
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
DEFAULT_MODEL = _env_str("GEMINI_OMNI_MODEL", "gemini-omni-1.2-flash")
FILES_API_BASE_URL = _env_str(
    "GEMINI_FILES_API_BASE_URL",
    "https://generativelanguage.googleapis.com/files",
)

# Video duration & reference limits (Gemini Omni 1.2 Flash)
MIN_DURATION_SECONDS = 3
MAX_DURATION_SECONDS = 15
MAX_KEYFRAME_DURATION_SECONDS = 10
MAX_RECOMMENDED_REF_VIDEOS = 3
MAX_15S_REF_VIDEOS = 1
MAX_TOTAL_EXTENDED_SECONDS = 40

# Supported output & task enumerations
DEFAULT_ASPECT_RATIO = "16:9"
SUPPORTED_ASPECT_RATIOS = ("16:9", "9:16")
SUPPORTED_RESOLUTIONS = ("360p", "720p", "1080p", "4k")
SUPPORTED_TASKS = (
    "text_to_video",
    "image_to_video",
    "reference_to_video",
    "edit",
    "extend",
)

# Output & temporary file paths
DEFAULT_OUTPUT_PATH = "media/output.mp4"
DEFAULT_BATCH_OUTPUT_DIR = "media"
TEMP_STRIPPED_PREFIX = "omni_stripped_"

# Timeouts & retry bounds
DEFAULT_HTTP_TIMEOUT_SECONDS = _env_int("GEMINI_OMNI_HTTP_TIMEOUT_SECONDS", 600)
FFMPEG_STRIP_AUDIO_TIMEOUT_SECONDS = _env_int(
    "GEMINI_OMNI_FFMPEG_TIMEOUT_SECONDS", 300
)
PREP_VIDEO_SUBPROCESS_TIMEOUT_SECONDS = _env_int(
    "GEMINI_OMNI_PREP_TIMEOUT_SECONDS", 600
)
UPLOAD_HTTP_TIMEOUT_MS = _env_int("GEMINI_OMNI_UPLOAD_HTTP_TIMEOUT_MS", 300000)
POLL_HTTP_TIMEOUT_MS = _env_int("GEMINI_OMNI_POLL_HTTP_TIMEOUT_MS", 30000)
FILE_POLL_INTERVAL_SECONDS = _env_int("GEMINI_OMNI_FILE_POLL_INTERVAL_SECONDS", 3)
FILE_POLL_MAX_ATTEMPTS = _env_int("GEMINI_OMNI_FILE_POLL_MAX_ATTEMPTS", 60)
FILE_POLL_BACKOFF_FACTOR = 1.2
FILE_POLL_MAX_INTERVAL_SECONDS = _env_int(
    "GEMINI_OMNI_FILE_POLL_MAX_INTERVAL_SECONDS", 15
)
FILE_POLL_MAX_TIMEOUT_SECONDS = _env_int(
    "GEMINI_OMNI_FILE_POLL_MAX_TIMEOUT_SECONDS", 600
)
FILE_POLL_MAX_CONSECUTIVE_ERRORS = _env_int(
    "GEMINI_OMNI_FILE_POLL_MAX_ERRORS", 5
)

# File upload size thresholds
BYTES_PER_MB = 1024 * 1024
LARGE_VIDEO_WARN_BYTES = _env_int(
    "GEMINI_OMNI_LARGE_VIDEO_WARN_BYTES", 25 * BYTES_PER_MB
)
NON_INTERACTIVE_MAX_VIDEO_BYTES = _env_int(
    "GEMINI_OMNI_NON_INTERACTIVE_MAX_VIDEO_BYTES", 100 * BYTES_PER_MB
)

# Parallel batch execution & single-instance lock bounds
DEFAULT_BATCH_CONCURRENCY = 3
MAX_BATCH_CONCURRENCY = _env_int("GEMINI_OMNI_MAX_CONCURRENCY", 10)
BATCH_LOCK_FILE_PATH = _env_str(
    "GEMINI_OMNI_BATCH_LOCK",
    os.path.join(tempfile.gettempdir(), "gemini_omni_generate_video_batch.lock"),
)

# Sanitization & formatting thresholds
MIN_REDACT_KEY_LENGTH = 8
MAX_SANITIZED_ERROR_LENGTH = 500
TRUNCATION_ELLIPSIS = "..."
MAX_SLUG_LENGTH = 50
MAX_LOGGED_PROMPT_LENGTH = 500
SHORT_LOG_PROMPT_LENGTH = 120
BATCH_LOG_PROMPT_LENGTH = 80
