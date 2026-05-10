"""V5 memory/extract.py — Block H memory extraction.

PORT_LOG: #095 (H-1..H-7 memory extraction core).

Source: Runnable services/extractMemories.ts + v4 sagemaker_agent.py
_extract_and_append_memories.

Per ADR-034: v5 lands the closure-scoped throttle state pattern that
v4's single-shot extraction lacked. Combines:
- v4's session-end trigger (writes memory.md when session ends).
- Runnable's hasMemoryWritesSince race guard (H-1).
- Runnable's countModelVisibleMessagesSince cursor fallback (H-2).
- Runnable's in-flight extraction tracking + drainPendingExtraction (H-3).
- Runnable's turnsSinceLastExtraction throttle (H-4).
- Runnable's createAutoMemCanUseTool scoped permission (H-5, advisory only —
  v5 doesn't grant tools to a memory extractor LLM in unit-test mode).
- Runnable's scanMemoryFiles + formatMemoryManifest pre-injected (H-6).
- Runnable's countToolCallsSince thresholded extraction (H-7).
"""
from __future__ import annotations

import os
import shlex
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# H-4: turn-throttle threshold. Wait at least N turns between extractions.
# Runnable default 5; v5 keeps the same.
DEFAULT_TURNS_SINCE_LAST_EXTRACTION = 5

# H-7: tool-call threshold. Extract at "natural break" — after N tool calls
# elapsed without an extraction. Runnable extractMemories.ts:316.
DEFAULT_TOOL_CALL_THRESHOLD = 25


READ_ONLY_TOOL_NAMES = {
    "read",
    "read_file",
    "grep",
    "glob",
    "ls",
    "listdir",
    "list_dir",
}
WRITE_TOOL_NAMES = {"edit", "write", "edit_file", "write_file"}


def _resolve_under(base: str, candidate: str) -> bool:
    if not candidate:
        return False
    try:
        base_path = Path(base).resolve()
        candidate_path = Path(candidate).resolve()
        candidate_path.relative_to(base_path)
        return True
    except Exception:
        return False


def _tool_path(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return ""
    for key in ("path", "file_path", "filepath", "target_path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def _is_readonly_bash_command(command: str) -> bool:
    try:
        parts = shlex.split(command or "", posix=False)
    except ValueError:
        return False
    if not parts:
        return False
    program = Path(parts[0]).name.lower()
    if program in {"cat", "type", "more", "less", "head", "tail", "findstr", "select-string", "rg", "grep", "dir", "ls", "pwd", "get-content", "get-childitem"}:
        return True
    return False


def create_auto_mem_can_use_tool(memory_dir: str) -> Callable[[str, Any], bool]:
    """H-5: scoped permissions for the auto-memory extractor.

    Read/Grep/Glob/listing tools are allowed because the extractor needs to
    inspect project memory context. Edit/Write are constrained to `memory_dir`.
    Bash is allowed only for simple read-only inspection commands.
    """

    def can_use(tool_name: str, tool_input: Any = None) -> bool:
        name = (tool_name or "").strip().lower()
        if name in READ_ONLY_TOOL_NAMES:
            return True
        if name in WRITE_TOOL_NAMES:
            return _resolve_under(memory_dir, _tool_path(tool_input))
        if name == "bash":
            command = ""
            if isinstance(tool_input, dict):
                command = str(tool_input.get("command") or "")
            elif isinstance(tool_input, str):
                command = tool_input
            return _is_readonly_bash_command(command)
        return False

    return can_use


def _make_set_event() -> threading.Event:
    """Helper: create an Event that starts in the SET state (idle)."""
    e = threading.Event()
    e.set()
    return e


@dataclass
class MemoryExtractor:
    """Per-session closure-scoped extraction state.

    H-1 race guard: `_in_flight` boolean — only one extraction running at
    a time; concurrent calls return early.
    H-2 cursor fallback: `_last_extracted_message_index` — when set, only
    messages AFTER this cursor are eligible for the next extraction.
    H-3 drain support: `_in_flight_lock` — drain_pending_extraction blocks
    until the in-flight extraction completes.
    H-4 turn throttle: `_turns_since_last_extraction` increments per agent
    turn; reset on extraction.
    H-7 tool-call threshold: `_tool_calls_since_last_extraction` increments
    per tool dispatch; reset on extraction.
    """
    workspace: str
    memory_path: str = "memory.md"
    turns_since_threshold: int = DEFAULT_TURNS_SINCE_LAST_EXTRACTION
    tool_call_threshold: int = DEFAULT_TOOL_CALL_THRESHOLD

    # closure-scoped state — never mutated outside this dataclass.
    _last_extracted_message_index: int = -1
    _turns_since_last_extraction: int = 0
    _tool_calls_since_last_extraction: int = 0
    _in_flight: bool = False
    _in_flight_lock: threading.Lock = field(default_factory=threading.Lock)
    # Codex iter-1 finding #2 BLOCKER fix: drain support requires an Event
    # signaled when the in-flight extraction completes. _in_flight_lock alone
    # is released the moment we set _in_flight=True, so a drain caller would
    # see "lock free, _in_flight True" and exit immediately. The Event
    # remains "unset" while in-flight and is set in the finally block.
    _idle_event: threading.Event = field(default_factory=lambda: _make_set_event())

    def has_memory_writes_since(self, last_known_index: int) -> bool:
        """H-1 race guard: did anything happen between `last_known_index`
        and the current extraction cursor that would change memory state?

        Used by sessionMemoryCompact to coordinate compaction with a
        pending extraction. Returns True iff `_last_extracted_message_index`
        has advanced since `last_known_index`.
        """
        return self._last_extracted_message_index > last_known_index

    def count_model_visible_messages_since(
        self,
        messages: List[Dict[str, Any]],
        cursor_index: int,
    ) -> int:
        """H-2 cursor fallback. Counts user/assistant messages AFTER
        cursor_index that are model-visible (not synthetic). Without this
        cursor fallback, mid-session extraction would lose track of which
        messages were already processed and re-extract everything (or
        permanently disable extraction)."""
        if cursor_index < 0:
            return sum(
                1 for m in messages
                if m.get("role") in ("user", "assistant")
                and not m.get("_synthetic")
            )
        return sum(
            1 for m in messages[cursor_index + 1:]
            if m.get("role") in ("user", "assistant")
            and not m.get("_synthetic")
        )

    def increment_turn(self) -> None:
        """H-4: call once per agent turn (success or failure)."""
        self._turns_since_last_extraction += 1

    def increment_tool_call(self) -> None:
        """H-7: call once per tool dispatch."""
        self._tool_calls_since_last_extraction += 1

    def should_extract(self, messages: List[Dict[str, Any]]) -> bool:
        """Return True iff extraction should run now.

        Triggers:
        - H-4: at least N turns since last extraction.
        - H-7: at least M tool calls since last extraction.
        - H-2: at least 1 model-visible message since last cursor.
        - H-1: no extraction currently in flight.
        """
        if self._in_flight:
            return False
        if self._turns_since_last_extraction < self.turns_since_threshold:
            return False
        if self._tool_calls_since_last_extraction < self.tool_call_threshold:
            return False
        if self.count_model_visible_messages_since(
            messages, self._last_extracted_message_index
        ) == 0:
            return False
        return True

    def scan_memory_files(self) -> List[str]:
        """H-6: list existing memory file basenames so the extraction
        prompt can pre-inject the manifest. Walks `workspace`.

        Returns sorted list of relative paths under workspace.
        """
        ws = Path(self.workspace)
        if not ws.is_dir():
            return []
        out: List[str] = []
        for fp in sorted(ws.rglob("*.md")):
            try:
                rel = fp.relative_to(ws)
                out.append(str(rel).replace("\\", "/"))
            except Exception:
                continue
        return out

    def format_memory_manifest(self) -> str:
        """H-6: format the manifest the extraction prompt sees."""
        files = self.scan_memory_files()
        if not files:
            return "(no existing memory files)"
        return "Existing memory files:\n" + "\n".join(f"- {f}" for f in files)

    def extract_memories(
        self,
        messages: List[Dict[str, Any]],
        extract_fn: Optional[Callable[[List[Dict], str], List[str]]] = None,
        force: bool = False,
    ) -> List[str]:
        """Run the extraction. Returns the list of new memory entries
        written to memory.md.

        Args:
            messages: full session message buffer.
            extract_fn: callable that takes (eligible_messages, manifest)
                and returns list of new memory strings. When None, runs
                a stub that extracts nothing — the v4 fallback for
                test mode where we don't dispatch a real LLM. Tests
                inject a mock here.
            force: skip the should_extract gate (used by session-end
                trigger).
        """
        if not force and not self.should_extract(messages):
            return []

        # H-1: in-flight guard. Set under lock so concurrent should_extract
        # callers see _in_flight=True before we start.
        # Codex iter-1 fix (drain): clear the idle Event under the lock so
        # drain_pending_extraction sees "in flight" reliably. Set the Event
        # again in the finally block.
        with self._in_flight_lock:
            if self._in_flight:
                return []
            self._in_flight = True
            self._idle_event.clear()

        try:
            # H-2: only consider messages AFTER the last extraction cursor.
            cursor = self._last_extracted_message_index
            eligible = (
                messages[cursor + 1:] if cursor >= 0 else list(messages)
            )
            if not eligible:
                return []

            manifest = self.format_memory_manifest()

            if extract_fn is None:
                # No LLM in test mode; return empty. Session-end caller
                # decides whether that is an error.
                new_entries: List[str] = []
            else:
                new_entries = list(extract_fn(eligible, manifest))

            # H-1: write iff we got entries.
            if new_entries:
                self._append_to_memory_md(new_entries)
                self._last_extracted_message_index = len(messages) - 1

            # Reset throttles on every extraction attempt — even empty
            # — so we don't immediately re-attempt.
            self._turns_since_last_extraction = 0
            self._tool_calls_since_last_extraction = 0
            return new_entries
        finally:
            # Codex iter-1 fix: signal idle under lock so a concurrent
            # drain_pending_extraction sees a consistent (in_flight,
            # idle_event) state.
            with self._in_flight_lock:
                self._in_flight = False
                self._idle_event.set()

    def drain_pending_extraction(self, timeout_s: float = 5.0) -> bool:
        """H-3: pre-shutdown drain. Block until any in-flight extraction
        completes, up to `timeout_s` seconds. Returns True iff drained
        cleanly (no in-flight at exit).

        Codex iter-1 finding #2 fix: use a threading.Event signaled in
        extract_memories' finally block. The previous lock-based approach
        was a no-op because _in_flight_lock is released the moment we
        set _in_flight=True — drain would acquire the free lock and
        return immediately while extraction was still running.
        """
        # Fast-path: already idle.
        if self._idle_event.is_set() and not self._in_flight:
            return True
        # Wait for the event to be set (signaled in finally clause above).
        # `wait` returns True if the event got set within timeout.
        return self._idle_event.wait(timeout=timeout_s)

    def _append_to_memory_md(self, entries: List[str]) -> None:
        """Write `entries` to memory.md atomically (best-effort)."""
        path = os.path.join(self.workspace, self.memory_path)
        try:
            existing = ""
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    existing = f.read()
            payload = existing
            if existing and not existing.endswith("\n"):
                payload += "\n"
            payload += "\n## Auto-extracted (Block H)\n"
            for e in entries:
                payload += f"- {e}\n"
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
        except OSError:
            # Memory writes are best-effort; never break the agent loop.
            pass


def create_memory_extractor(workspace: str, **kwargs: Any) -> MemoryExtractor:
    """Factory that returns a MemoryExtractor bound to the given workspace."""
    return MemoryExtractor(workspace=workspace, **kwargs)


def extract_memories(
    extractor: MemoryExtractor,
    messages: List[Dict[str, Any]],
    extract_fn: Optional[Callable[[List[Dict], str], List[str]]] = None,
    force: bool = False,
) -> List[str]:
    """Functional wrapper around MemoryExtractor.extract_memories — kept
    for backwards compat with v4's procedural API.
    """
    return extractor.extract_memories(messages, extract_fn=extract_fn, force=force)
