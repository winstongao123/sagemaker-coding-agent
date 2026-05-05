"""Block H context and onboarding helpers.

Ports the remaining Runnable context/onboarding rows in a v5 sync-friendly
shape. The helpers are best-effort: context improves prompts, but import or git
failures must not break the agent loop.
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


_SYSTEM_CONTEXT_CACHE: Dict[str, tuple[float, str]] = {}


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _walk_from_workspace(workspace: Path, current_dir: Path) -> Iterable[Path]:
    current = current_dir.resolve()
    root = workspace.resolve()
    try:
        current.relative_to(root)
    except ValueError:
        current = root

    chain: List[Path] = []
    while True:
        chain.append(current)
        if current == root or current.parent == current:
            break
        current = current.parent
    return reversed(chain)


def get_user_context(
    workspace: str,
    current_dir: Optional[str] = None,
    filenames: Iterable[str] = ("CLAUDE.md",),
    max_chars: int = 16000,
) -> str:
    """H-18: aggregate CLAUDE.md-style files from workspace to cwd."""
    root = Path(workspace)
    cur = Path(current_dir) if current_dir else root
    blocks: List[str] = []
    seen: Set[Path] = set()
    for directory in _walk_from_workspace(root, cur):
        for name in filenames:
            path = directory / name
            resolved = path.resolve()
            if resolved in seen or not path.is_file():
                continue
            seen.add(resolved)
            try:
                text = path.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue
            if text:
                blocks.append(f"### {_safe_relative(path, root)}\n{text}")

    if not blocks:
        return ""
    body = "## User Context\n\n" + "\n\n".join(blocks)
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + "\n...[truncated]"
    return body


def get_system_context(
    workspace: str,
    max_chars: int = 2000,
    memo_ttl_s: float = 5.0,
) -> str:
    """H-19: memoized git-status system context, capped at 2K chars."""
    root = str(Path(workspace).resolve())
    now = time.monotonic()
    cached = _SYSTEM_CONTEXT_CACHE.get(root)
    if cached and now - cached[0] <= memo_ttl_s:
        return cached[1]

    status = _read_git_status(root)
    if not status:
        _SYSTEM_CONTEXT_CACHE[root] = (now, "")
        return ""

    body = "## System Context\n\nGit status (`--no-optional-locks --short`):\n\n```text\n"
    body += status.strip()
    body += "\n```"
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + "\n...[truncated]"
    _SYSTEM_CONTEXT_CACHE[root] = (now, body)
    return body


def _read_git_status(workspace: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "-C", workspace, "status", "--short"],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


@dataclass
class OnboardingState:
    """H-20: simple first-run onboarding state with auto-suppress."""

    completed_steps: Set[str] = field(default_factory=set)
    suppressed: bool = False
    steps: List[str] = field(default_factory=lambda: [
        "workspace",
        "status",
        "verify",
        "memory",
    ])

    @classmethod
    def from_file(cls, path: str) -> "OnboardingState":
        file_path = Path(path)
        if not file_path.is_file():
            return cls()
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return cls()
        steps = data.get("steps")
        if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
            steps = cls().steps
        completed = data.get("completed_steps", [])
        if not isinstance(completed, list):
            completed = []
        state = cls(
            completed_steps={s for s in completed if isinstance(s, str)},
            suppressed=bool(data.get("suppressed", False)),
            steps=list(steps),
        )
        state.auto_suppress_if_complete()
        return state

    def to_file(self, path: str) -> None:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "steps": list(self.steps),
            "completed_steps": sorted(self.completed_steps),
            "suppressed": self.suppressed,
        }
        file_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def mark_complete(self, step: str) -> None:
        if step in self.steps:
            self.completed_steps.add(step)
        self.auto_suppress_if_complete()

    def next_step(self) -> Optional[str]:
        if self.suppressed:
            return None
        for step in self.steps:
            if step not in self.completed_steps:
                return step
        return None

    def auto_suppress_if_complete(self) -> None:
        if all(step in self.completed_steps for step in self.steps):
            self.suppressed = True


def should_show_onboarding(state: OnboardingState) -> bool:
    return state.next_step() is not None
