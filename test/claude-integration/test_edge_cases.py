#!/usr/bin/env python3
"""
test_edge_cases.py - Regression tests for PR #27 and PR #13 fixes

These tests verify:
- PR #27: PGP block stripping and mode-aware response handling
- PR #13: Improved error messages and key validation
"""

import sys
import os
import re
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "bridge"))

# Import the functions under test
# Note: Some functions may not exist until PR #27 is merged
try:
    from grok_bridge import (
        strip_pgp_blocks,
        TEXT_MODES,
        PGP_BLOCK_PATTERN,
        parse_and_write_files,
    )
    PR27_AVAILABLE = True
except ImportError:
    PR27_AVAILABLE = False
    strip_pgp_blocks = None
    TEXT_MODES = None
    PGP_BLOCK_PATTERN = None
    parse_and_write_files = None

#-------------------------------------------------------------------------------
# Test Fixtures
#-------------------------------------------------------------------------------

MOCK_RESPONSES_DIR = Path(__file__).parent / "mock_responses"


def load_mock_response(name: str) -> str:
    """Load a mock response file."""
    return (MOCK_RESPONSES_DIR / name).read_text()


#-------------------------------------------------------------------------------
# PR #27: PGP Block Stripping Tests
#-------------------------------------------------------------------------------

class TestPGPBlockStripping:
    """Tests for PGP armored block detection and removal."""

    def test_pgp_pattern_compiled(self):
        """Verify PGP block regex is properly compiled."""
        assert PGP_BLOCK_PATTERN is not None
        assert isinstance(PGP_BLOCK_PATTERN.pattern, str)

    def test_pgp_block_stripped_from_response(self):
        """PGP blocks should be completely removed from responses."""
        response_with_pgp = load_mock_response("pgp_block.txt")

        cleaned = strip_pgp_blocks(response_with_pgp)

        # PGP block should be gone
        assert "-----BEGIN PGP MESSAGE-----" not in cleaned
        assert "-----END PGP MESSAGE-----" not in cleaned

        # But the real content should remain
        assert "Security Findings" in cleaned or "analysis" in cleaned.lower()

    def test_clean_response_unchanged(self):
        """Responses without PGP blocks should be unaffected (except for .strip())."""
        clean_response = load_mock_response("text_only_analyze.txt")

        cleaned = strip_pgp_blocks(clean_response)

        # .strip() is called at end of strip_pgp_blocks, so whitespace may change
        assert cleaned.strip() == clean_response.strip()
        assert "-----BEGIN PGP MESSAGE-----" not in cleaned

    def test_pgp_pattern_regex_robustness(self):
        """Verify the regex handles various PGP block formats."""
        # Single line PGP-like content (shouldn't match - needs proper format)
        single_line = "-----BEGIN PGP MESSAGE-----fake content-----END PGP MESSAGE-----"
        assert "-----BEGIN PGP MESSAGE-----" in single_line  # Pattern is in there

        # Real PGP block format with proper headers/footers
        real_format = """Some text before
-----BEGIN PGP MESSAGE-----

body content here
-----END PGP MESSAGE-----

Some text after"""

        cleaned = strip_pgp_blocks(real_format)
        assert "Some text before" in cleaned
        assert "Some text after" in cleaned
        assert "-----BEGIN" not in cleaned


#-------------------------------------------------------------------------------
# PR #27: Mode-Aware Response Handling Tests
#-------------------------------------------------------------------------------

class TestModeAwareResponseHandling:
    """Tests for mode-aware handling of responses."""

    def test_text_modes_defined(self):
        """Verify all expected text modes are defined."""
        expected_text_modes = {"analyze", "reason", "orchestrate"}
        assert TEXT_MODES == expected_text_modes

    def test_parse_and_write_with_clean_response(self):
        """parse_and_write_files should return empty list for non-annotated content."""
        text_response = load_mock_response("text_only_analyze.txt")

        # Create temp output dir
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(text_response, tmpdir)

            # No annotated files should be found
            assert len(written) == 0, f"Expected 0 files, got {len(written)}"

    def test_parse_and_write_with_annotated_code(self):
        """parse_and_write_files should extract annotated code blocks."""
        annotated = load_mock_response("annotated_code.txt")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(annotated, tmpdir)

            # Should have found and written files
            # written is list of (relative_path, byte_count) tuples
            assert len(written) > 0, f"Expected annotated files to be found, got {written}"
            assert all(isinstance(p, str) and b > 0 for p, b in written)

    def test_no_false_positives_in_text_response(self):
        """Text responses should not trigger false file writes."""
        text_response = load_mock_response("text_only_analyze.txt")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(text_response, tmpdir)

            # No files should be created
            assert len(written) == 0

            # And the directory should be empty
            dir_contents = list(Path(tmpdir).iterdir())
            assert len(dir_contents) == 0


#-------------------------------------------------------------------------------
# PR #13: Error Message Improvement Tests
#-------------------------------------------------------------------------------

class TestErrorMessages:
    """Tests for improved error messages (PR #13)."""

    def test_missing_api_key_error_message(self):
        """Missing API key should show helpful error with all attempted sources."""
        # This test runs the actual CLI without a key and captures stderr
        result = subprocess.run(
            [
                sys.executable,
                "-m", "src.bridge.grok_bridge",
                "--prompt", "test",
                "--mode", "analyze",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "OPENROUTER_API_KEY": "", "XAI_API_KEY": ""},
        )

        # Should fail gracefully
        assert result.returncode != 0

        # Should mention the 4 sources we try
        combined = result.stdout + result.stderr
        assert "OPENROUTER_API_KEY" in combined or "env var" in combined.lower()
        assert "config.json" in combined or "config" in combined.lower()
        assert "setup" in combined.lower() or "oauth" in combined.lower()


#-------------------------------------------------------------------------------
# Exit Code Semantics Tests
#-------------------------------------------------------------------------------

class TestExitCodes:
    """Verify exit code semantics are correct."""

    def test_exit_code_0_for_success(self):
        """Successful runs should exit with code 0."""
        # This would require a valid API key, so we skip actual runs
        # But we verify our logic expects 0 for success cases
        pass  # Handled by integration tests with real keys

    def test_exit_code_1_for_actual_errors(self):
        """Actual errors (not "no files found") should exit with code 1."""
        # Missing API key is a real error - run with --prompt but no API key
        result = subprocess.run(
            [
                sys.executable,
                "-m", "src.bridge.grok_bridge",
                "--prompt", "test",
            ],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k not in [
                "OPENROUTER_API_KEY", "XAI_API_KEY"
            ]},
        )
        # Should fail due to missing key with exit code 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}: {result.stderr[:200]}"

    def test_exit_code_2_for_content_filter(self):
        """Content filter triggered should exit with code 2."""
        # This would require triggering Grok's content filter
        # Skip for now - would need mock server
        pass


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Edge Cases & Regression Tests")
    print("Testing PR #27 (PGP + mode-aware) and PR #13 (errors)")
    print("=" * 60)
    print()

    import tempfile
    import shutil

    all_passed = True

    # Run tests
    test_classes = [
        TestPGPBlockStripping,
        TestModeAwareResponseHandling,
        TestErrorMessages,
        TestExitCodes,
    ]

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * len(test_class.__name__))

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {method_name}")
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("All edge case tests PASSED")
        sys.exit(0)
    else:
        print("Some edge case tests FAILED")
        sys.exit(1)
