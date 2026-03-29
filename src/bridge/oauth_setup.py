#!/usr/bin/env python3
"""
oauth_setup.py — PKCE OAuth helper for Grok Swarm / OpenRouter.

The API key NEVER passes through Claude's context window.
Flow: browser → OpenRouter → localhost:3000 → ~/.config/grok-swarm/config.json

Usage:
    python3 oauth_setup.py            # interactive PKCE OAuth flow
    python3 oauth_setup.py --check    # exit 0 if key exists, 1 if not (no output)
    python3 oauth_setup.py --provider xai  # print manual setup instructions

Requirements: Python 3.8+ stdlib only (no third-party packages).
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import socket
import sys
import tempfile
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import List, Tuple

# OpenRouter OAuth constants
OPENROUTER_AUTH_URL = "https://openrouter.ai/auth"
OPENROUTER_TOKEN_URL = "https://openrouter.ai/api/v1/auth/keys"
CALLBACK_PORT = 3000  # OpenRouter only allows localhost:3000
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}"
APP_NAME = "Grok+Swarm"
OAUTH_TIMEOUT_SECS = 180

CONFIG_DIR = Path.home() / ".config" / "grok-swarm"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def _generate_pkce_pair() -> Tuple[str, str]:
    """Return (code_verifier, code_challenge)."""
    verifier_bytes = secrets.token_bytes(64)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


# ---------------------------------------------------------------------------
# Key persistence
# ---------------------------------------------------------------------------

def _key_exists() -> bool:
    """Return True if an API key is already configured."""
    # Check env vars first
    if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("XAI_API_KEY"):
        return True
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return bool(data.get("api_key"))
        except (json.JSONDecodeError, OSError):
            pass
    # Also check ~/.claude/grok-swarm.local.md
    claude_settings = Path.home() / ".claude" / "grok-swarm.local.md"
    if claude_settings.exists():
        try:
            for line in claude_settings.read_text(encoding="utf-8").splitlines():
                if line.startswith("api_key:") and line.split(":", 1)[1].strip():
                    return True
        except OSError:
            pass
    return False


def _save_key(api_key: str) -> None:
    """Write API key to ~/.config/grok-swarm/config.json with mode 600."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if CONFIG_FILE.exists():
        try:
            existing = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    existing["api_key"] = api_key

    # Write to a temporary file with secure permissions, then atomically rename
    json_bytes = (json.dumps(existing, indent=2) + "\n").encode("utf-8")
    fd = os.open(
        str(CONFIG_DIR / f".config.json.tmp.{os.getpid()}"),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600
    )
    try:
        os.write(fd, json_bytes)
        os.fsync(fd)
    finally:
        os.close(fd)

    # Atomically replace the target file
    os.replace(str(CONFIG_DIR / f".config.json.tmp.{os.getpid()}"), str(CONFIG_FILE))


# ---------------------------------------------------------------------------
# OAuth callback server
# ---------------------------------------------------------------------------

_received_code: List[str] = []


class _CallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that captures the ?code= query parameter."""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        if code:
            _received_code.append(code)
            body = b"<html><body><h2>Grok Swarm authorized!</h2><p>You can close this tab.</p></body></html>"
            self.send_response(200)
        else:
            body = b"<html><body><h2>Authorization failed.</h2><p>No code received. Please try again.</p></body></html>"
            self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # type: ignore[override]
        pass  # suppress request logs


def _exchange_code(code: str, code_verifier: str) -> str:
    """Exchange auth code for API key via OpenRouter token endpoint."""
    payload = json.dumps({"code": code, "code_verifier": code_verifier}).encode()
    req = urllib.request.Request(
        OPENROUTER_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        raise RuntimeError(f"Token exchange failed: {exc}") from exc

    key = data.get("key") or data.get("api_key")
    if not key:
        raise RuntimeError(f"No key in response: {data}")
    return key


def _check_port_available() -> bool:
    """Return True if localhost:3000 is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("localhost", CALLBACK_PORT)) != 0


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def run_oauth_flow() -> int:
    """
    Run the PKCE OAuth flow.

    Returns 0 on success, 1 on failure.
    """
    # Clear any stale codes from previous runs
    _received_code.clear()

    if not _check_port_available():
        print(
            f"ERROR: Port {CALLBACK_PORT} is already in use.\n"
            f"Stop whatever is using port {CALLBACK_PORT} and retry, or set your key manually:\n"
            f"  mkdir -p ~/.config/grok-swarm\n"
            f"  echo '{{\"api_key\": \"sk-or-v1-...\"}}' > ~/.config/grok-swarm/config.json\n"
            f"  chmod 600 ~/.config/grok-swarm/config.json",
            file=sys.stderr,
        )
        return 1

    code_verifier, code_challenge = _generate_pkce_pair()

    auth_params = urllib.parse.urlencode(
        {
            "callback_url": CALLBACK_URL,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "app_name": APP_NAME,
        }
    )
    auth_url = f"{OPENROUTER_AUTH_URL}?{auth_params}"

    print("=" * 60)
    print("Grok Swarm — OpenRouter Authorization")
    print("=" * 60)
    print()
    print("Click the link below to authorize Grok Swarm with your")
    print("OpenRouter account (or paste it into your browser):")
    print()
    print(f"  {auth_url}")
    print()
    print(f"Waiting up to {OAUTH_TIMEOUT_SECS}s for authorization callback...")

    # Handle bind-time races: another process may have bound between the
    # _check_port_available call and this HTTPServer creation.
    max_retries = 3
    server = None
    for attempt in range(max_retries):
        try:
            server = HTTPServer(("localhost", CALLBACK_PORT), _CallbackHandler)
            server.timeout = OAUTH_TIMEOUT_SECS
            break
        except OSError as exc:
            if attempt < max_retries - 1:
                __import__("time").sleep(0.5)
                continue
            # Final attempt failed
            print(
                f"\nERROR: Failed to bind to port {CALLBACK_PORT} after {max_retries} attempts: {exc}",
                file=sys.stderr,
            )
            print("Please try again or set your key manually:", file=sys.stderr)
            print("  export OPENROUTER_API_KEY=sk-or-v1-...", file=sys.stderr)
            return 1

    deadline = __import__("time").time() + OAUTH_TIMEOUT_SECS
    while not _received_code and __import__("time").time() < deadline:
        server.handle_request()

    server.server_close()

    if not _received_code:
        print("\nERROR: Timed out waiting for authorization.", file=sys.stderr)
        print("Please try again or set your key manually:", file=sys.stderr)
        print("  export OPENROUTER_API_KEY=sk-or-v1-...", file=sys.stderr)
        return 1

    code = _received_code[0]
    print("\nCallback received. Exchanging code for API key...", end=" ", flush=True)

    try:
        api_key = _exchange_code(code, code_verifier)
    except RuntimeError as exc:
        print(f"FAILED\nERROR: {exc}", file=sys.stderr)
        return 1

    try:
        _save_key(api_key)
    except OSError as exc:
        print(f"FAILED\nERROR: Could not save API key to {CONFIG_FILE}: {exc}", file=sys.stderr)
        return 1

    print(f"OK\n\nSuccess! API key saved to {CONFIG_FILE}")
    return 0


def run_check() -> int:
    """Exit 0 if key exists, 1 if not. No output."""
    return 0 if _key_exists() else 1


def print_manual_instructions() -> None:
    """Print instructions for manually placing xAI / OpenRouter credentials."""
    print("""Grok Swarm — Manual Credential Setup
=====================================

Option A — OpenRouter (recommended):
  1. Create an account at https://openrouter.ai
  2. Generate an API key at https://openrouter.ai/keys
  3. Run one of:

     export OPENROUTER_API_KEY=sk-or-v1-...

     # or save permanently:
     mkdir -p ~/.config/grok-swarm
     echo '{"api_key": "sk-or-v1-..."}' > ~/.config/grok-swarm/config.json
     chmod 600 ~/.config/grok-swarm/config.json

Option B — xAI direct (no OAuth available):
  1. Create an account at https://console.x.ai
  2. Generate an API key in your dashboard
  3. Run one of:

     export XAI_API_KEY=xai-...

     # or save permanently (grok_bridge will read the "api_key" field from config.json):
     mkdir -p ~/.config/grok-swarm
     echo '{"api_key": "xai-..."}' > ~/.config/grok-swarm/config.json
     chmod 600 ~/.config/grok-swarm/config.json

     Note: when using xAI direct you must also update grok_bridge.py's
     OPENROUTER_BASE to point to https://api.x.ai/v1
""")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set up OpenRouter API key for Grok Swarm via PKCE OAuth."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if key already configured, 1 otherwise (no output).",
    )
    parser.add_argument(
        "--provider",
        choices=["openrouter", "xai"],
        default="openrouter",
        help="Credential provider. 'xai' prints manual instructions (no OAuth).",
    )
    args = parser.parse_args()

    if args.check:
        sys.exit(run_check())

    if args.provider == "xai":
        print_manual_instructions()
        sys.exit(0)

    sys.exit(run_oauth_flow())


if __name__ == "__main__":
    main()