"""
grok-swarm-agent - Autonomous agent wrapper for Grok 4.20.

This module provides an iterative agent loop that:
1. Receives natural language tasks
2. Discovers relevant files
3. Calls Grok 4.20 via grok_bridge
4. Parses code blocks and applies changes
5. Verifies changes with tests
6. Iterates until done or max iterations reached

Cross-platform: works with both Claude Code and OpenClaw.
"""

from .grok_agent import main, run_agent_loop, AgentState, Platform, AgentStatus

__all__ = ["main", "run_agent_loop", "AgentState", "Platform", "AgentStatus"]
