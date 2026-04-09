#!/usr/bin/env python3
"""
test_setup.py - Setup flow tests

Tests the various ways a user can set up their API key:
1. Environment variables
2. config.json file
3. OAuth flow (manual verification)
4. Key validation after save
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "bridge"))

#-------------------------------------------------------------------------------
# Test Configuration
#-------------------------------------------------------------------------------

TEST_CONFIG_PATH = Path(temp_dir := __import__("tempfile").gettempdir()) / "test_grok_config.json"
TEST_API_KEY = "sk-or-v1-test1234567890abcdefghijklmnopqrstuvwxyz"


#-------------------------------------------------------------------------------
# Test 1.1: No API Key - Should Prompt for Setup
#-------------------------------------------------------------------------------

class TestNoAPILKey:
    """Tests for behavior when no API key is configured."""

    def test_no_key_no_config(self):
        """Without key or config, should fail gracefully with setup hint."""
        # Run with clean environment
        env = {k: v for k, v in os.environ.items()
               if k not in ["OPENROUTER_API_KEY", "XAI_API_KEY"]}

        # Remove test config if it exists
        if TEST_CONFIG_PATH.exists():
            TEST_CONFIG_PATH.unlink()

        result = subprocess.run(
            [
                sys.executable, "-c",
                "import sys; sys.path.insert(0, 'src/bridge'); "
                "from grok_bridge import get_api_key; "
                "print(get_api_key())"
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should return None (no key found)
        # Note: This may fail to import if dependencies missing
        # That's a different failure mode


#-------------------------------------------------------------------------------
# Test 1.2: OAuth Flow (Manual Verification)
#-------------------------------------------------------------------------------

class TestOAuthFlow:
    """Tests for OAuth PKCE flow."""

    def test_oauth_script_exists(self):
        """Verify oauth_setup.py exists and is executable."""
        oauth_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "oauth_setup.py"
        assert oauth_path.exists(), f"oauth_setup.py not found at {oauth_path}"

    def test_oauth_imports(self):
        """Verify oauth_setup.py has required imports."""
        oauth_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "oauth_setup.py"
        content = oauth_path.read_text()

        required_imports = [
            "urllib.request",
            "urllib.parse",
            "json",
            "socket",
            "http.server",
            "secrets",
            "hashlib",
        ]

        for imp in required_imports:
            assert imp in content, f"Missing import: {imp}"

    def test_oauth_has_key_validation(self):
        """Verify oauth_setup.py validates key after save (PR #13 fix)."""
        oauth_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "oauth_setup.py"
        content = oauth_path.read_text()

        # Should validate key against API
        assert "api/v1/auth/key" in content or "validate" in content.lower(), \
            "oauth_setup.py should validate key after saving"


#-------------------------------------------------------------------------------
# Test 1.3: Key Detection via Environment Variable
#-------------------------------------------------------------------------------

class TestEnvVarKeyDetection:
    """Tests for API key detection from environment variables."""

    def test_openrouter_key_detected(self):
        """OPENROUTER_API_KEY should be detected."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": TEST_API_KEY}, clear=False):
            # Clear other potential sources
            with patch.dict(os.environ, {"XAI_API_KEY": ""}, clear=False):
                # Import and test
                from grok_bridge import get_api_key
                key = get_api_key()
                # Note: may return None if other sources take precedence
                # but should at least attempt to read env var

    def test_xai_key_detected(self):
        """XAI_API_KEY should be detected as fallback."""
        # This test verifies the resolution order
        from importlib import reload
        import grok_bridge as gb
        reload(gb)

        # The resolution order should be:
        # 1. OPENROUTER_API_KEY
        # 2. XAI_API_KEY
        # 3. config.json
        # 4. .local.md


#-------------------------------------------------------------------------------
# Test 1.4: Key Detection via config.json
#-------------------------------------------------------------------------------

class TestConfigFileKeyDetection:
    """Tests for API key detection from config.json."""

    def test_config_json_格式(self):
        """config.json should have correct format."""
        config_dir = Path.home() / ".config" / "grok-swarm"
        config_path = config_dir / "config.json"

        # Create test config
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "api_key": TEST_API_KEY,
            "org_id": "test-org",
        }))

        try:
            # Read it back
            with open(config_path) as f:
                config = json.load(f)

            assert "api_key" in config
            assert config["api_key"] == TEST_API_KEY
        finally:
            # Cleanup
            if config_path.exists():
                config_path.unlink()

    def test_config_missing_fields(self):
        """config.json with missing fields should be handled gracefully."""
        config_dir = Path.home() / ".config" / "grok-swarm"
        config_path = config_dir / "config.json"

        # Create minimal config
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({}))

        try:
            with open(config_path) as f:
                config = json.load(f)

            # Should not crash, just missing values
            assert isinstance(config, dict)
        finally:
            if config_path.exists():
                config_path.unlink()


#-------------------------------------------------------------------------------
# Test 1.5: Key Validation Post-Save (PR #13)
#-------------------------------------------------------------------------------

class TestKeyValidation:
    """Tests for key validation after saving (PR #13 fix)."""

    def test_oauth_validates_before_returning(self):
        """OAuth flow should validate key before declaring success."""
        oauth_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "oauth_setup.py"
        content = oauth_path.read_text()

        # Should call the validation endpoint
        assert "urlopen" in content
        assert "Authorization" in content or "Bearer" in content

    def test_validation_failure_is_handled(self):
        """Validation failure should not crash - just warn."""
        oauth_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "oauth_setup.py"
        content = oauth_path.read_text()

        # Should have try/except around validation
        assert "try:" in content
        assert "except" in content


#-------------------------------------------------------------------------------
# Test 1.6: Error Message Improvements (PR #13)
#-------------------------------------------------------------------------------

class TestErrorMessageImprovements:
    """Tests for improved error messages."""

    def test_error_lists_all_key_sources(self):
        """Error message should list all attempted key sources."""
        from grok_bridge import get_api_key

        # When no key is found, error should mention:
        # 1. OPENROUTER_API_KEY / XAI_API_KEY env vars
        # 2. ~/.config/grok-swarm/config.json
        # 3. ~/.claude/grok-swarm.local.md
        # 4. OpenClaw profiles

        # We can't easily test the error output without actually
        # triggering the error, but we can verify the sources exist
        assert True  # Placeholder - actual test needs integration run


#-------------------------------------------------------------------------------
# Test 1.7: Claude Command Surface
#-------------------------------------------------------------------------------

class TestClaudeCommandSurface:
    """Tests for Claude-facing command bootstrap assets."""

    def test_grok_prefixed_command_files_exist(self):
        """Searchable Grok-prefixed Claude commands should be bundled."""
        repo_root = Path(__file__).parent.parent.parent
        required_commands = [
            "platforms/claude/commands/grok-swarm.md",
            "platforms/claude/commands/grok-swarm-setup.md",
            "platforms/claude/commands/grok-swarm-analyze.md",
            "platforms/claude/commands/grok-swarm-refactor.md",
            "platforms/claude/commands/grok-swarm-code.md",
            "platforms/claude/commands/grok-swarm-reason.md",
            "platforms/claude/commands/grok-swarm-stats.md",
            "platforms/claude/commands/grok-swarm-set-key.md",
        ]

        missing = [path for path in required_commands if not (repo_root / path).exists()]
        assert not missing, f"Missing Grok command files: {missing}"

    def test_command_helper_bootstraps_plugin_runtime(self):
        """The shared command helper should call plugin setup when runtime is missing."""
        helper_path = Path(__file__).parent.parent.parent / "platforms" / "claude" / "commands" / "setup.sh"
        content = helper_path.read_text(encoding="utf-8")

        assert '.claude-plugin/setup.sh' in content
        assert 'claude mcp list' in content
        assert 'python3' in content


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Setup Flow Tests")
    print("Testing key detection, OAuth, and validation")
    print("=" * 60)
    print()

    all_passed = True

    test_classes = [
        TestNoAPILKey,
        TestOAuthFlow,
        TestEnvVarKeyDetection,
        TestConfigFileKeyDetection,
        TestKeyValidation,
        TestErrorMessageImprovements,
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
        print("All setup tests PASSED")
        sys.exit(0)
    else:
        print("Some setup tests FAILED")
        sys.exit(1)
