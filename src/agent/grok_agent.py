#!/usr/bin/env python3
"""
grok_agent.py — Autonomous agent loop powered by Grok 4.20.

Minimal viable agent loop:
1. Receive task + target
2. Discover files
3. Call grok_bridge with context
4. Parse response for file operations
5. Apply changes (or preview)
6. Verify (if verify_cmd provided)
7. Iterate or report

Cross-platform: --platform claude or --platform openclaw

Usage:
    python3 grok_agent.py --task "refactor auth module" --target ./src/auth
    python3 grok_agent.py --task "analyze security" --target ./src --apply
    python3 grok_agent.py --task "add tests" --target . --apply --verify-cmd "pytest"
"""

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# Import existing bridge (sibling to agent/ directory)
sys.path.insert(0, str(Path(__file__).parent.parent / "bridge"))
from grok_bridge import call_grok, read_files

# Import shared patterns
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from patterns import get_filename_pattern_string


class Platform(Enum):
    CLAUDE = "claude"
    OPENCLAW = "openclaw"


class AgentStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    NO_FILES = "no_files"


@dataclass
class AgentState:
    """Agent execution state."""
    task: str
    target: str
    platform: Platform
    apply: bool = False
    max_iterations: int = 5
    verify_cmd: Optional[str] = None
    output_dir: Optional[str] = None

    iteration: int = 0
    status: AgentStatus = AgentStatus.RUNNING
    changes: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    # Shared context across iterations
    file_context: str = ""
    last_response: str = ""
    last_verification_output: str = ""


# =============================================================================
# Path Sanitization
# =============================================================================

def sanitize_target_path(path_hint: str, base_root: str) -> Path:
    """
    Sanitize a path hint to prevent directory traversal and absolute path attacks.

    Args:
        path_hint: The path provided by the LLM (should be relative)
        base_root: The base directory to write to (target or output_dir)

    Returns:
        A safe resolved Path within base_root

    Raises:
        ValueError: If the path is unsafe (absolute, escapes root, etc.)
    """
    # Reject or strip leading "/" and "~"
    hint = path_hint.strip()
    if hint.startswith("/"):
        hint = hint.lstrip("/")
    if hint.startswith("~"):
        raise ValueError(f"Cannot use home directory paths: {path_hint}")

    # Convert to Path and check for absolute
    raw_path = Path(hint)
    if raw_path.is_absolute():
        raise ValueError(f"Cannot use absolute paths: {path_hint}")

    # Get the base root and resolve it
    root = Path(base_root)
    if root.is_file():
        # If target is a file, use its parent as root
        root = root.parent
    root = root.resolve()

    # Build the target path and resolve it
    target_path = (root / raw_path).resolve()

    # Check if resolved path is within the root
    try:
        target_path.relative_to(root)
    except ValueError:
        raise ValueError(f"Path escapes target directory: {path_hint} -> {target_path}")

    return target_path


# =============================================================================
# File Discovery
# =============================================================================

def discover_files(target: str, max_files: int = 50) -> list[str]:
    """
    Discover relevant code files in target directory.

    Supports: .py, .js, .ts, .tsx, .jsx, .go, .rs, .java, .c, .cpp, .h, .hpp
    """
    path = Path(target)
    if not path.exists():
        return []

    if path.is_file():
        return [str(path)]

    # Language extensions to search for
    extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
    }

    files = []
    for ext in extensions:
        files.extend([str(p) for p in path.glob(f"**/*{ext}")])

    # Sort by path length (shorter = more likely root-level) and limit
    files.sort(key=lambda f: (len(Path(f).parts), f))
    return files[:max_files]


# =============================================================================
# Code Block Parsing (Fixed from grok_bridge.py issues)
# =============================================================================

def parse_code_blocks(response_text: str) -> list[dict]:
    """
    Parse code blocks from Grok response.

    Supports multiple annotation formats:
      ```python:/path/to/file.py
      # content
      ```

      ```python
      // FILE: /path/to/file.py
      # content
      ```

      ```python
      # FILE: /path/to/file.py
      # content
      ```

      ```python
      # filename.py
      # content
      ```

    Returns list of dicts with keys: language, path_hint, content, inferred_path
    """
    blocks = []

    # Pattern 1: lang:/path/to/file (language tag contains path)
    lang_path_pattern = re.compile(r'^(\w+):(/[^/\s\n]+(?:/[^/\s\n]+)*)\n', re.MULTILINE)

    # Pattern 2: // FILE: /path or # FILE: /path
    file_marker_pattern = re.compile(
        r'^\s*(?:(?://|#)\s*)FILE:\s*(.+?)\s*$',
        re.MULTILINE
    )

    # Pattern 3: # filename.py (just filename as first line comment)
    filename_pattern = re.compile(get_filename_pattern_string(), re.MULTILINE)

    # Split into code blocks by ``` fences
    parts = re.split(r'```', response_text)

    for i, part in enumerate(parts):
        if i % 2 == 0:
            continue

        # Get first line (may contain language or markers)
        first_line_end = part.find('\n')
        if first_line_end == -1:
            first_line_end = len(part)

        first_line = part[:first_line_end]
        rest = part[first_line_end + 1:]

        language = ""
        path_hint = ""
        content = rest

        # Check pattern 1: lang:/path
        lang_match = lang_path_pattern.match(part)
        if lang_match:
            language = lang_match.group(1)
            path_hint = lang_match.group(2)
            content = part[lang_match.end():]
            blocks.append({
                "language": language,
                "path_hint": path_hint,
                "content": content.strip(),
                "inferred_path": path_hint.split('/')[-1] if '/' in path_hint else path_hint
            })
            continue

        # Check for language in first line (e.g., "python")
        lang_candidate = first_line.strip()
        if lang_candidate and lang_candidate.isalpha():
            language = lang_candidate

        # Check pattern 1b: lang:path on first line (e.g., "python:cli.py" with no trailing newline)
        lang_path_on_line = re.compile(r'^(\w+):([^\s\n]+)')
        line_match = lang_path_on_line.match(first_line)
        if line_match:
            language = line_match.group(1)
            path_hint = line_match.group(2)
            content = rest
            blocks.append({
                "language": language,
                "path_hint": path_hint,
                "content": content.strip(),
                "inferred_path": path_hint.split('/')[-1] if '/' in path_hint else path_hint
            })
            continue

        # Check pattern 2: // FILE: or # FILE:
        # Only search the first non-empty line of rest
        rest_lines = rest.split('\n')
        first_non_lang_line = ""
        first_line_idx = 0
        for idx, line in enumerate(rest_lines):
            if line.strip():
                first_non_lang_line = line
                first_line_idx = idx
                break

        marker_match = file_marker_pattern.search(first_non_lang_line) if first_non_lang_line else None
        if marker_match:
            path_hint = marker_match.group(1).strip()
            # Remove the marker line from content
            content = '\n'.join(rest_lines[first_line_idx + 1:])
            blocks.append({
                "language": language,
                "path_hint": path_hint,
                "content": content.strip(),
                "inferred_path": path_hint.split('/')[-1] if '/' in path_hint else path_hint
            })
            continue

        # Check pattern 3: # filename.py
        # Only search the first non-empty line of rest
        filename_match = filename_pattern.search(first_non_lang_line) if first_non_lang_line else None
        if filename_match:
            filename = filename_match.group(1)
            path_hint = filename
            # Remove the filename line from content
            content = '\n'.join(rest_lines[first_line_idx + 1:])
            blocks.append({
                "language": language,
                "path_hint": path_hint,
                "content": content.strip(),
                "inferred_path": filename
            })

    return blocks


def parse_and_write_files(response_text: str, output_dir: str) -> list[tuple]:
    """
    Parse code blocks and write files to output_dir.

    Returns list of (relative_path, byte_count) tuples.
    """
    written = []
    output_path = Path(output_dir)

    blocks = parse_code_blocks(response_text)

    for block in blocks:
        path_hint = block.get("path_hint", "")
        content = block.get("content", "")

        if not path_hint or not content:
            continue

        # Sanitize path
        try:
            dest = sanitize_target_path(path_hint, output_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            encoded = content.strip().encode("utf-8", errors="replace")
            dest.write_bytes(encoded)
            written.append((str(Path(path_hint)), len(encoded)))
        except ValueError as e:
            print(f"WARNING: Skipping unsafe path: {e}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Failed to write {path_hint}: {e}", file=sys.stderr)

    return written


# =============================================================================
# File Application
# =============================================================================

def apply_file_change(file_path: str, content: str, dry_run: bool = True) -> bool:
    """
    Apply a file change to the actual target directory.

    Args:
        file_path: Relative path within target
        content: File content to write
        dry_run: If True, just preview; if False, actually write
    """
    if dry_run:
        print(f"[PREVIEW] Would write {file_path} ({len(content)} chars)")
        return True

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text(content)
        print(f"[WROTE] {file_path}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}", file=sys.stderr)
        return False


def apply_changes_from_response(state: AgentState, response: str) -> list[str]:
    """
    Parse response for code blocks and apply to target directory.

    Returns list of files that were (or would be) written.
    """
    blocks = parse_code_blocks(response)
    applied = []

    if not blocks:
        # Check if there's any content that looks like code without annotations
        if "```" in response:
            print("[WARNING] Code blocks found but no file annotations - cannot apply", file=sys.stderr)
        return applied

    for block in blocks:
        path_hint = block.get("path_hint", "")
        content = block.get("content", "")

        if not path_hint:
            # Try to infer from language
            lang = block.get("language", "")
            if lang:
                ext = {"python": "py", "javascript": "js", "typescript": "ts", "go": "go"}.get(lang.lower(), lang.lower())
                path_hint = f"generated.{ext}"
                print(f"[WARNING] No path for {lang} block, using {path_hint}", file=sys.stderr)
            else:
                continue

        # Sanitize and apply in target directory
        try:
            # Determine if this is a new file by checking existence in target directory
            # First resolve path_hint relative to state.target to check if file exists
            temp_target_path = sanitize_target_path(path_hint, state.target)
            is_new_file = not temp_target_path.exists()

            # Use output_dir only for new files, otherwise use target
            base_root = state.output_dir if (state.output_dir and is_new_file) else state.target
            target_path = sanitize_target_path(path_hint, base_root)

            if state.apply:
                success = apply_file_change(str(target_path), content, dry_run=False)
                if success:
                    applied.append(str(target_path))
            else:
                apply_file_change(str(target_path), content, dry_run=True)
                applied.append(str(target_path))
        except ValueError as e:
            print(f"[ERROR] Skipping unsafe path: {e}", file=sys.stderr)
            continue

    return applied


# =============================================================================
# Verification
# =============================================================================

def verify_changes(state: AgentState) -> tuple[bool, str]:
    """
    Run verification command.

    Returns (success, output).
    """
    if not state.verify_cmd:
        return True, "No verification command"

    try:
        result = subprocess.run(
            state.verify_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=state.target,
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Verification timed out (>120s)"
    except Exception as e:
        return False, str(e)


# =============================================================================
# Agent Loop
# =============================================================================

def build_agent_prompt(state: AgentState) -> str:
    """Build the prompt for Grok based on current state."""
    task = state.task

    if state.iteration == 1:
        # First iteration: discover and plan
        files = discover_files(state.target)
        state.file_context = read_files(files) if files else ""

        file_count = len(files) if files else 0

        # Get just the first 30K chars to avoid overwhelming Grok
        context_preview = state.file_context[:30000] if state.file_context else ""

        return f"""You are an autonomous coding agent. Your task: {task}

Target: {state.target} ({file_count} files)

{context_preview}

CRITICAL FORMAT - Write files using this EXACT format:
```python:cli.py
# full content here
```
or:
```python
// FILE: cli.py
# full content here
```

Do NOT use just `# filename.py`. Do NOT use no annotation.
"""
    else:
        # Subsequent iterations: refine based on previous
        prompt = f"""Continue working on: {task}

Previous iteration ({state.iteration - 1}) response:
{state.last_response[:15000]}

Iteration {state.iteration}/{state.max_iterations}"""

        # Include verification output if available
        if state.last_verification_output:
            prompt += f"""

Verifier output / failure:
{state.last_verification_output[:5000]}
"""

        prompt += """

If the previous changes had errors or could be improved, refine them. Otherwise, continue with the next set of changes.

Use the same annotation format:
```python:/path/to/file.py
# content
```
"""
        return prompt


def run_iteration(state: AgentState) -> bool:
    """
    Run a single agent iteration.

    Returns True if agent should stop (done or success).
    """
    state.iteration += 1
    print(f"\n=== Iteration {state.iteration}/{state.max_iterations} ===", file=sys.stderr)

    # Build prompt
    prompt = build_agent_prompt(state)

    # Call Grok
    print("Calling Grok 4.20 (refactor mode)...", file=sys.stderr)
    try:
        response = call_grok(
            prompt=prompt,
            mode="refactor",
            timeout=180,
        )
        state.last_response = response
    except SystemExit as se:
        error_msg = f"Grok call failed with exit code {se.code}"
        state.errors.append(error_msg)
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False
    except Exception as e:
        state.errors.append(f"Grok call failed: {e}")
        print(f"[ERROR] Grok call failed: {e}", file=sys.stderr)
        return False

    # Parse and apply changes
    if state.apply:
        applied = apply_changes_from_response(state, response)
        state.changes.extend(applied)
        print(f"Applied {len(applied)} files", file=sys.stderr)
    else:
        # Preview mode
        blocks = parse_code_blocks(response)
        print(f"[PREVIEW] Would modify {len(blocks)} blocks", file=sys.stderr)

    # Verify if command provided
    verification_succeeded = True  # Default to True if no verification
    if state.verify_cmd and state.apply:
        success, output = verify_changes(state)
        verification_succeeded = success
        state.last_verification_output = output  # Store for next iteration
        if success:
            print("[VERIFY] Passed", file=sys.stderr)
        else:
            state.errors.append(f"Verification failed: {output[:500]}")
            print(f"[VERIFY] Failed: {output[:500]}", file=sys.stderr)
            # Continue anyway - Grok can fix in next iteration

    # Check if done - but only if verification passed
    response_lower = response.lower()
    done_markers = ["done", "complete", "finished", "all changes made", "successfully"]
    if verification_succeeded and any(marker in response_lower for marker in done_markers):
        return True

    # Check if no changes were made
    blocks = parse_code_blocks(response)
    if not blocks and state.iteration > 1:
        return True

    return False


def run_agent_loop(state: AgentState) -> AgentState:
    """Run the full agent loop until completion or max iterations."""
    print("[AGENT] Starting agent loop", file=sys.stderr)
    print(f"[AGENT] Task: {state.task}", file=sys.stderr)
    print(f"[AGENT] Target: {state.target}", file=sys.stderr)
    print(f"[AGENT] Apply mode: {state.apply}", file=sys.stderr)

    # Check target exists
    if not Path(state.target).exists():
        state.status = AgentStatus.NO_FILES
        state.errors.append(f"Target does not exist: {state.target}")
        return state

    # Check files exist
    files = discover_files(state.target)
    if not files:
        state.status = AgentStatus.NO_FILES
        state.errors.append(f"No code files found in: {state.target}")
        return state

    while state.iteration < state.max_iterations:
        done = run_iteration(state)
        if done:
            state.status = AgentStatus.SUCCESS
            break
    else:
        state.status = AgentStatus.MAX_ITERATIONS

    return state


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Grok Swarm Agent - Autonomous agent powered by Grok 4.20",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview mode (default) - shows what would change
  python3 grok_agent.py --task "refactor auth module" --target ./src/auth

  # Apply changes
  python3 grok_agent.py --task "refactor auth module" --target ./src/auth --apply

  # With verification
  python3 grok_agent.py --task "add tests" --target ./src --apply --verify-cmd "pytest"

  # OpenClaw platform
  python3 grok_agent.py --platform openclaw --task "analyze security" --target .
        """
    )
    parser.add_argument("--platform", choices=["claude", "openclaw"], default="claude",
                       help="Platform (default: claude)")
    parser.add_argument("--target", default=".",
                       help="Target directory or file (default: .)")
    parser.add_argument("--apply", action="store_true",
                       help="Actually apply changes (default: preview mode)")
    parser.add_argument("--max-iterations", type=int, default=5,
                       help="Max agent iterations (default: 5)")
    parser.add_argument("--verify-cmd",
                       help="Command to run for verification (e.g., pytest)")
    parser.add_argument("--output-dir",
                       help="Output directory for new files (existing files remain in target)")
    parser.add_argument("--task", "-t", required=True, dest="task",
                       help="Natural language task instruction")

    args = parser.parse_args()

    # Create state
    state = AgentState(
        task=args.task,
        target=args.target,
        platform=Platform(args.platform),
        apply=args.apply,
        max_iterations=args.max_iterations,
        verify_cmd=args.verify_cmd,
        output_dir=args.output_dir,
    )

    # Run agent
    result = run_agent_loop(state)

    # Output summary
    print("\n" + "=" * 60, file=sys.stderr)
    print("GROK-SWARM-AGENT SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Status:     {result.status.value}", file=sys.stderr)
    print(f"Iterations: {result.iteration}/{result.max_iterations}", file=sys.stderr)
    print(f"Files:      {len(result.changes)} changed", file=sys.stderr)

    if result.changes:
        print("\nChanged files:", file=sys.stderr)
        for f in result.changes:
            print(f"  - {f}", file=sys.stderr)

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):", file=sys.stderr)
        for err in result.errors:
            print(f"  - {err[:200]}", file=sys.stderr)

    print("=" * 60, file=sys.stderr)

    if result.apply:
        # Show human-readable summary to stdout
        if result.status == AgentStatus.SUCCESS:
            print(f"✓ Completed in {result.iteration} iteration(s)")
            print(f"✓ Changed {len(result.changes)} file(s)")
        elif result.status == AgentStatus.MAX_ITERATIONS:
            print(f"⚠ Max iterations ({result.max_iterations}) reached")
            print(f"  Changed {len(result.changes)} file(s) - may need more work")
        elif result.status == AgentStatus.NO_FILES:
            print(f"✗ No files found in target: {result.target}")
        else:
            print(f"✗ Failed: {result.errors[0] if result.errors else 'Unknown error'}")
    else:
        # Preview mode
        print("\n[PREVIEW MODE] Re-run with --apply to actually write changes")

    sys.exit(0 if result.status == AgentStatus.SUCCESS else 1)


if __name__ == "__main__":
    main()