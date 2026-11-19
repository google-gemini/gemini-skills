#!/usr/bin/env python3
import pathlib
import sys
import unittest

# Ensure scripts and scripts/video are on sys.path
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "skills" / "gemini-omni-flash-api" / "scripts"
VIDEO_DIR = SCRIPTS_DIR / "video"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(VIDEO_DIR))

from inspect_video import format_size, parse_fps
from prep_video import parse_timecode, prep_video
from unittest.mock import patch
from generate_video import (
    normalize_file_uri,
    parse_and_validate_resolution,
    sanitize_error,
)


class TestVideoScripts(unittest.TestCase):
    """Unit tests for video utilities and helpers in gemini-omni-flash-api skill."""

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 1024), "1.00 TB")
        self.assertEqual(format_size(-100), "Unknown size")
        self.assertEqual(format_size("invalid"), "Unknown size")
        self.assertEqual(format_size(None), "Unknown size")

    def test_parse_fps(self):
        self.assertEqual(parse_fps("30/1"), "30 fps")
        self.assertEqual(parse_fps("24000/1001"), "23.98 fps")
        self.assertEqual(parse_fps("60"), "60 fps")
        self.assertEqual(parse_fps("29.97"), "29.97 fps")
        self.assertEqual(parse_fps("0/0"), "Unknown")
        self.assertEqual(parse_fps("0"), "Unknown")
        self.assertEqual(parse_fps("0 fps"), "Unknown")
        self.assertEqual(parse_fps("-24"), "Unknown")
        self.assertEqual(parse_fps(""), "Unknown")
        self.assertEqual(parse_fps(None), "Unknown")
        self.assertEqual(parse_fps("invalid/text"), "Unknown")

    def test_parse_timecode_valid(self):
        self.assertEqual(parse_timecode(""), 0.0)
        self.assertEqual(parse_timecode(None), 0.0)
        self.assertEqual(parse_timecode("0"), 0.0)
        self.assertEqual(parse_timecode("12.5"), 12.5)
        self.assertEqual(parse_timecode("01:30"), 90.0)
        self.assertEqual(parse_timecode("02:00:00"), 7200.0)
        self.assertEqual(parse_timecode("01:02:03"), 3723.0)

    def test_parse_timecode_last(self):
        # Default 10s target duration
        self.assertEqual(parse_timecode("last", total_duration=30.0), 20.0)
        # Custom 5s target duration
        self.assertEqual(parse_timecode("last", total_duration=30.0, target_duration=5.0), 25.0)
        # Short video: returns 0.0
        self.assertEqual(parse_timecode("last", total_duration=8.0, target_duration=10.0), 0.0)
        # Missing total_duration
        with self.assertRaises(ValueError):
            parse_timecode("last", total_duration=None)

    def test_parse_timecode_invalid(self):
        # Negative seconds
        with self.assertRaises(ValueError):
            parse_timecode("-5")
        # Negative components in MM:SS
        with self.assertRaises(ValueError):
            parse_timecode("-01:30")
        with self.assertRaises(ValueError):
            parse_timecode("01:-30")
        # Seconds out of range (>=60)
        with self.assertRaises(ValueError):
            parse_timecode("01:65")
        with self.assertRaises(ValueError):
            parse_timecode("01:75:00")
        # Malformed colon formats
        with self.assertRaises(ValueError):
            parse_timecode("1:2:3:4")
        with self.assertRaises(ValueError):
            parse_timecode("not_a_time")

    def test_normalize_file_uri(self):
        self.assertEqual(
            normalize_file_uri("files/abc123xyz"),
            "https://generativelanguage.googleapis.com/files/abc123xyz",
        )
        self.assertEqual(
            normalize_file_uri("files/asset_123-abc"),
            "https://generativelanguage.googleapis.com/files/asset_123-abc",
        )
        self.assertEqual(
            normalize_file_uri("https://generativelanguage.googleapis.com/files/abc123xyz?key=test&auth=123"),
            "https://generativelanguage.googleapis.com/files/abc123xyz",
        )
        self.assertIsNone(normalize_file_uri(None))
        self.assertIsNone(normalize_file_uri(""))

    def test_parse_and_validate_resolution(self):
        for res in ["360p", "720p", "1080p", "4k"]:
            self.assertEqual(parse_and_validate_resolution(res), res)
            self.assertEqual(parse_and_validate_resolution(res.upper()), res)
        self.assertIsNone(parse_and_validate_resolution(None))
        self.assertIsNone(parse_and_validate_resolution(""))
        self.assertIsNone(parse_and_validate_resolution("none"))
        with self.assertRaises(ValueError):
            parse_and_validate_resolution("480p")
        with self.assertRaises(ValueError):
            parse_and_validate_resolution("8k")

    def test_sanitize_error(self):
        self.assertEqual(sanitize_error(""), "")
        self.assertEqual(sanitize_error(None), "")
        # Redacts Google API keys
        err = "Failed request with AIzaSyD3xAmPlEkEy1234567890abcdefgh"
        sanitized = sanitize_error(err)
        self.assertNotIn("AIzaSyD3xAmPlEkEy1234567890abcdefgh", sanitized)
        self.assertIn("[REDACTED_KEY]", sanitized)
        # Redacts Bearer tokens
        err_token = "Unauthorized: Bearer ya29.a0AfH6SMTestToken123456"
        sanitized_token = sanitize_error(err_token)
        self.assertNotIn("ya29.a0AfH6SMTestToken123456", sanitized_token)

    @patch("prep_video.subprocess.run")
    @patch("prep_video.inspect_video")
    @patch("os.path.exists", return_value=True)
    def test_prep_video_validation_guards(self, mock_exists, mock_inspect, mock_run):
        # 1. Non-positive duration guard
        mock_inspect.return_value = {"has_video": True, "duration_seconds": 30.0}
        with self.assertRaises(ValueError) as cm:
            prep_video("input.mp4", "output.mp4", duration=0)
        self.assertIn("Duration must be a positive number", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            prep_video("input.mp4", "output.mp4", duration=-5)
        self.assertIn("Duration must be a positive number", str(cm.exception))

        # 2. Audio-only / no video stream guard
        mock_inspect.return_value = {"has_video": False, "duration_seconds": 30.0}
        with self.assertRaises(ValueError) as cm:
            prep_video("audio_only.mp4", "output.mp4", duration=10)
        self.assertIn("does not contain a valid video stream", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
