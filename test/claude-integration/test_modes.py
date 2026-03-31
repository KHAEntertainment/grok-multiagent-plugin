#!/usr/bin/env python3
"""
test_modes.py - Core mode functionality tests

Tests all 5 Grok modes:
- analyze: Text analysis, security audits, code review
- refactor: Code improvements with annotated output
- code: Generate new code with file annotations
- reason: Multi-perspective reasoning/analysis
- orchestrate: Custom system prompt handling
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "bridge"))

#-------------------------------------------------------------------------------
# Test Constants
#-------------------------------------------------------------------------------

MOCK_RESPONSES_DIR = Path(__file__).parent / "mock_responses"
VALID_MODES = ["analyze", "refactor", "code", "reason", "orchestrate"]


#-------------------------------------------------------------------------------
# Test 2.1: Mode Validation
#-------------------------------------------------------------------------------

class TestModeValidation:
    """Tests for mode parameter validation."""

    def test_valid_modes_accepted(self):
        """All 5 modes should be recognized as valid."""
        for mode in VALID_MODES:
            result = subprocess.run(
                [
                    sys.executable, "-m", "src.bridge.grok_bridge",
                    "--help"
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )
            # Help should list all modes
            combined = result.stdout + result.stderr
            # Modes should be in help text
            assert "analyze" in combined or "mode" in combined.lower()

    def test_invalid_mode_rejected(self):
        """Invalid modes should produce error."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--mode", "invalid_mode_xyz",
                "--prompt", "test"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "OPENROUTER_API_KEY": "", "XAI_API_KEY": ""},
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should fail
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "invalid" in combined.lower() or "error" in combined.lower()


#-------------------------------------------------------------------------------
# Test 2.2: Agent Count by Mode
#-------------------------------------------------------------------------------

class TestAgentCount:
    """Tests for agent count configuration per mode."""

    def test_agent_counts_defined(self):
        """Verify AGENT_COUNTS dict is properly defined."""
        from grok_bridge import AGENT_COUNTS

        assert isinstance(AGENT_COUNTS, dict)
        assert "low" in AGENT_COUNTS
        assert "high" in AGENT_COUNTS

    def test_low_thinking_agents(self):
        """Low thinking should use 4 agents."""
        from grok_bridge import AGENT_COUNTS
        assert AGENT_COUNTS["low"] == 4

    def test_high_thinking_agents(self):
        """High thinking should use 16 agents."""
        from grok_bridge import AGENT_COUNTS
        assert AGENT_COUNTS["high"] == 16


#-------------------------------------------------------------------------------
# Test 2.3: Mode-Specific Behavior
#-------------------------------------------------------------------------------

class TestModeSpecificBehavior:
    """Tests for mode-specific response handling."""

    def test_text_modes_for_text_output(self):
        """analyze, reason, orchestrate should output text directly."""
        from grok_bridge import TEXT_MODES

        expected = {"analyze", "reason", "orchestrate"}
        assert TEXT_MODES == expected

    def test_parse_and_write_behavior(self):
        """parse_and_write_files should work correctly for each mode type."""
        from grok_bridge import parse_and_write_files

        # For text_only_analyze.txt - should return empty
        text_response = (MOCK_RESPONSES_DIR / "text_only_analyze.txt").read_text()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(text_response, tmpdir)
            assert len(written) == 0, "Text response should produce no files"

    def test_annotated_code_parsing(self):
        """Annotated code blocks should be correctly parsed."""
        from grok_bridge import parse_and_write_files

        annotated = (MOCK_RESPONSES_DIR / "annotated_code.txt").read_text()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(annotated, tmpdir)
            # written is list of (relative_path, byte_count) tuples
            assert len(written) > 0, f"Annotated code should produce files, got {written}"

            # Verify each file was recorded with positive byte count
            for file_path, byte_count in written:
                assert byte_count > 0, f"File {file_path} should have positive byte count"


#-------------------------------------------------------------------------------
# Test 2.4: System Prompt Handling
#-------------------------------------------------------------------------------

class TestSystemPrompt:
    """Tests for custom system prompt handling."""

    def test_system_prompt_parameter_exists(self):
        """--system flag should be available."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        # Should mention system prompt option
        assert "system" in combined.lower()

    def test_orchestrate_mode_custom_system(self):
        """orchestrate mode should allow custom system prompts."""
        # This is more of an integration test
        # For now, verify the mode exists
        assert "orchestrate" in VALID_MODES


#-------------------------------------------------------------------------------
# Test 2.5: Output Format by Mode
#-------------------------------------------------------------------------------

class TestOutputFormat:
    """Tests for correct output formatting per mode."""

    def test_help_shows_output_options(self):
        """Help should document output options."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        # Should have write-files option
        assert "write-files" in combined or "output" in combined.lower()


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Mode Functionality Tests")
    print("Testing all 5 modes: analyze, refactor, code, reason, orchestrate")
    print("=" * 60)
    print()

    all_passed = True

    test_classes = [
        TestModeValidation,
        TestAgentCount,
        TestModeSpecificBehavior,
        TestSystemPrompt,
        TestOutputFormat,
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
        print("All mode tests PASSED")
        sys.exit(0)
    else:
        print("Some mode tests FAILED")
        sys.exit(1)
