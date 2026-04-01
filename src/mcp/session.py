"""
session.py — Multi-turn session management for Grok Swarm MCP server.

Each GrokSession maintains a conversation history in OpenAI message format
and calls grok_bridge.call_grok_with_messages() for API requests.

Sessions are stored in-memory (scoped to the MCP server process lifetime).
"""

import logging
import secrets
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Ensure bridge is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from bridge.grok_bridge import call_grok_with_messages, MODE_PROMPTS

log = logging.getLogger("grok-mcp.session")

# ---------------------------------------------------------------------------
# Session configuration
# ---------------------------------------------------------------------------

SESSION_TTL_SECS = 1800  # 30 minutes
MAX_SESSIONS = 10
MAX_TOKEN_BUDGET = 500_000

# ---------------------------------------------------------------------------
# Session store
# ---------------------------------------------------------------------------

_sessions: Dict[str, "GrokSession"] = {}


class GrokSession:
    """A stateful multi-turn conversation with Grok."""

    __slots__ = (
        "session_id",
        "mode",
        "thinking",
        "system_prompt",
        "messages",
        "created_at",
        "last_active",
        "total_tokens",
        "max_tokens",
    )

    def __init__(
        self,
        session_id: str,
        mode: str = "reason",
        thinking: str = "low",
        system_prompt: str = "",
    ):
        self.session_id = session_id
        self.mode = mode
        self.thinking = thinking
        self.system_prompt = system_prompt
        # messages does NOT include the system message — that's prepended at call time
        self.messages: List[dict] = []
        self.created_at = time.time()
        self.last_active = time.time()
        self.total_tokens = 0
        self.max_tokens = MAX_TOKEN_BUDGET

    def send_message(self, user_content: str, file_context: str = "") -> str:
        """
        Send a user message and get Grok's response.

        Args:
            user_content: The user's message text.
            file_context: Optional file content to prepend to the message.

        Returns:
            Grok's response text.

        Raises:
            RuntimeError: If the session's token budget is exhausted.
            Exception: Propagated from the API on errors.
        """
        self.last_active = time.time()

        if self.total_tokens >= self.max_tokens:
            raise RuntimeError(
                f"Session {self.session_id} token budget exhausted "
                f"({self.total_tokens:,} / {self.max_tokens:,}). "
                "Start a new session."
            )

        # Build user message content
        content = user_content
        if file_context:
            content = f"## Additional File Context\n{file_context}\n\n{user_content}"

        self.messages.append({"role": "user", "content": content})

        # Build full message list for API
        api_messages = [{"role": "system", "content": self.system_prompt}]

        # Inject budget warning early (right after system prompt) for visibility
        if self.total_tokens > self.max_tokens * 0.8:
            api_messages.append({
                "role": "system",
                "content": (
                    "NOTE: Token budget for this session is nearly exhausted. "
                    "Please wrap up your response concisely."
                ),
            })

        api_messages.extend(self.messages)

        response = call_grok_with_messages(
            messages=api_messages,
            timeout=120,
            thinking=self.thinking,
            mode=self.mode,
        )

        # Track cumulative API token usage (for cost tracking).
        # Each turn's total_tokens includes re-sent history, so this reflects
        # actual API billing, not unique conversation size.
        if hasattr(response, "usage") and response.usage:
            self.total_tokens += response.usage.total_tokens

        # Extract assistant content
        if not response.choices:
            raise RuntimeError("Empty response from Grok API")

        assistant_content = response.choices[0].message.content or ""
        self.messages.append({"role": "assistant", "content": assistant_content})

        log.info(
            "Session %s: turn %d, tokens=%d/%d",
            self.session_id,
            len(self.messages) // 2,
            self.total_tokens,
            self.max_tokens,
        )

        return assistant_content

    def to_dict(self) -> dict:
        """Serialize session for optional persistence."""
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "thinking": self.thinking,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GrokSession":
        """Deserialize session from dict."""
        session = cls(
            session_id=data["session_id"],
            mode=data.get("mode", "reason"),
            thinking=data.get("thinking", "low"),
            system_prompt=data.get("system_prompt", ""),
        )
        session.messages = data.get("messages", [])
        session.created_at = data.get("created_at", time.time())
        session.last_active = data.get("last_active", time.time())
        session.total_tokens = data.get("total_tokens", 0)
        session.max_tokens = data.get("max_tokens", MAX_TOKEN_BUDGET)
        return session


# ---------------------------------------------------------------------------
# Session store management
# ---------------------------------------------------------------------------

def _evict_expired():
    """Remove sessions that have exceeded their TTL."""
    now = time.time()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s.last_active > SESSION_TTL_SECS
    ]
    for sid in expired:
        log.info("Evicting expired session: %s", sid)
        del _sessions[sid]


def create_session(
    mode: str = "reason",
    system_override: Optional[str] = None,
    thinking: str = "low",
    initial_file_context: str = "",
) -> GrokSession:
    """Create and register a new session."""
    _evict_expired()

    # Enforce max sessions
    if len(_sessions) >= MAX_SESSIONS:
        # Evict the oldest session
        oldest_id = min(_sessions, key=lambda sid: _sessions[sid].last_active)
        log.info("Evicting oldest session (max reached): %s", oldest_id)
        del _sessions[oldest_id]

    session_id = secrets.token_hex(8)

    # Build system prompt
    if system_override:
        system_prompt = system_override
    else:
        system_prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["reason"])
        if system_prompt is None:
            system_prompt = ""

    if initial_file_context:
        system_prompt += f"\n\n## Codebase Context\n{initial_file_context}"

    session = GrokSession(
        session_id=session_id,
        mode=mode,
        thinking=thinking,
        system_prompt=system_prompt,
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[GrokSession]:
    """Look up a session by ID, evicting expired ones first."""
    _evict_expired()
    session = _sessions.get(session_id)
    if session is not None:
        session.last_active = time.time()
    return session


def list_sessions() -> List[dict]:
    """Return summary info for all active sessions."""
    _evict_expired()
    return [
        {
            "session_id": s.session_id,
            "mode": s.mode,
            "thinking": s.thinking,
            "turns": len(s.messages) // 2,
            "total_tokens": s.total_tokens,
            "last_active": s.last_active,
        }
        for s in _sessions.values()
    ]
