"""Block C+ — PermissionDialog (approval flow + always-allow + reason prompt).

Renders a per-tool approval dialog when CONFIG.require_tool_approval=True
AND the tool's `requires_approval=True`. The dialog surfaces:
  - Tool name + sanitised parameters
  - Optional diff preview (edit_file / write_file via ui/diff_widget)
  - Optional reason string from tool_use args (Block C+ richer feature)
  - Block C UI-only helper warnings: cd+git compound bare-repo (C-11),
    multi-cd (C-12), per-pipe-segment destructive (C-13), bash comment-
    label (C-14) — all surfaced when bash is the dispatched tool
  - Three buttons: Approve / Deny / Always allow (per-tool sticky)

Block C+ headless contract: when ipywidgets is unavailable, the dialog
falls back to a synchronous text-mode `ask_user`-style prompt with a
60-second watchdog timeout.

PORT_LOG: see #064.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ApprovalResult:
    """The outcome of a single approval prompt."""

    approved: bool
    always_allow: bool = False  # if True, future calls to same tool skip the dialog
    reason: str = ""             # caller-supplied rationale for the decision
    timed_out: bool = False


@dataclass
class PermissionDialog:
    """Per-tool approval dialog. ipywidgets-aware with text fallback.

    Block C+ adds three features over the Phase-9 base:
      1. always_allow toggle — sticky per tool name, lives in
         CONFIG._always_allowed (initialized lazily).
      2. reason prompt — surfaces the tool_use input's `reason` field
         when present so the user understands intent before approving.
      3. Block-C bash safety annotations — cd+git, multi-cd,
         pipe-segment destructive warnings displayed inline.
    """

    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    diff_html: Optional[str] = None
    reason: str = ""

    # Watchdog timeout for headless / text-mode fallback.
    timeout_seconds: int = 60

    # Optional callable used by tests to short-circuit the modal loop.
    _override_decision: Optional[Callable[[], ApprovalResult]] = None

    # --------------------------------------------------------
    # Decision driver
    # --------------------------------------------------------

    def prompt(self) -> ApprovalResult:
        """Show the dialog + block until decided (or timed out).

        Resolution order (sticky FIRST so always-allow short-circuits
        even when callers pass an `_override_decision`):
          1. CONFIG._always_allowed[tool_name] — auto-approve if sticky.
          2. `_override_decision` — used by unit tests to inject answers.
          3. ipywidgets dialog (Approve / Deny / Always allow buttons).
          4. Text-mode fallback (ask_user-style) with watchdog timeout.
        """
        # 1) sticky always-allow (Block-C+ Codex finding lock test)
        from runtime.config import CONFIG
        if not hasattr(CONFIG, "_always_allowed"):
            CONFIG._always_allowed = {}
        if CONFIG._always_allowed.get(self.tool_name):
            return ApprovalResult(approved=True, always_allow=True,
                                  reason="sticky: tool was previously Always-allowed")

        # 2) test override
        if self._override_decision is not None:
            return self._override_decision()

        # 3) ipywidgets path
        try:
            from ui.chat_ui import _IPYWIDGETS_OK
        except Exception:
            _IPYWIDGETS_OK = False
        if _IPYWIDGETS_OK:
            return self._prompt_widgets()

        # 4) text-mode fallback (ask_user style with watchdog)
        return self._prompt_text_mode()

    # --------------------------------------------------------
    # Annotation: Block-C bash safety hooks
    # --------------------------------------------------------

    def render_warnings(self) -> List[str]:
        """Return human-readable warnings to display alongside the dialog.

        Block C UI-only helpers (C-11/C-12/C-13/C-14) surface here when
        the dispatched tool is `bash`. Per ADR-023 §Notes / known scope
        remaps (Block C UI-only helpers → Block C+).
        """
        warnings: List[str] = []
        if self.tool_name != "bash":
            return warnings
        cmd = self.parameters.get("command", "")
        if not cmd:
            return warnings
        try:
            from security.bash_safety import (
                destructive_command_warning,
                has_cd_git_compound_with_bare_repo,
                has_multiple_cd,
                pipe_segment_permission_check,
                extract_bash_comment_label,
            )
            d = destructive_command_warning(cmd)
            if d:
                warnings.append(f"⚠ destructive: {d}")
            if has_cd_git_compound_with_bare_repo(cmd):
                warnings.append("⚠ cd into bare git repo + git command (fsmonitor risk)")
            if has_multiple_cd(cmd):
                warnings.append("⚠ multiple cd's — chained directory changes")
            for seg_warn in pipe_segment_permission_check(cmd):
                warnings.append(f"⚠ pipe-segment destructive: {seg_warn}")
            label = extract_bash_comment_label(cmd)
            if label:
                warnings.append(f"label: {label}")
        except Exception:
            pass
        return warnings

    # --------------------------------------------------------
    # ipywidgets dialog
    # --------------------------------------------------------

    def _prompt_widgets(self) -> ApprovalResult:
        """Block on three-button ipywidgets dialog. Best-effort render."""
        try:
            import ipywidgets as widgets
            from IPython.display import display
        except Exception:
            return self._prompt_text_mode()

        decision: Dict[str, Any] = {"result": None}

        def on_approve(_btn):
            decision["result"] = ApprovalResult(approved=True)

        def on_deny(_btn):
            decision["result"] = ApprovalResult(approved=False, reason="user denied")

        def on_always(_btn):
            from runtime.config import CONFIG
            if not hasattr(CONFIG, "_always_allowed"):
                CONFIG._always_allowed = {}
            CONFIG._always_allowed[self.tool_name] = True
            decision["result"] = ApprovalResult(
                approved=True, always_allow=True,
                reason="user clicked Always-allow",
            )

        approve_btn = widgets.Button(description="Approve", button_style="success")
        deny_btn = widgets.Button(description="Deny", button_style="danger")
        always_btn = widgets.Button(description="Always allow this tool",
                                    button_style="warning")
        approve_btn.on_click(on_approve)
        deny_btn.on_click(on_deny)
        always_btn.on_click(on_always)

        header = f"<b>Approve `{self.tool_name}`?</b>"
        if self.reason:
            header += f"<br/><i>Reason from model:</i> {self.reason}"
        warning_lines = self.render_warnings()
        warning_html = "<br/>".join(warning_lines) if warning_lines else ""
        body_parts = [widgets.HTML(value=header)]
        if warning_html:
            body_parts.append(widgets.HTML(value=warning_html))
        if self.diff_html:
            body_parts.append(widgets.HTML(value=self.diff_html))
        body_parts.append(widgets.HBox([approve_btn, deny_btn, always_btn]))
        panel = widgets.VBox(body_parts)
        display(panel)

        # Spin until a button clicked or watchdog fires.
        deadline = time.time() + self.timeout_seconds
        while decision["result"] is None and time.time() < deadline:
            time.sleep(0.1)
        if decision["result"] is None:
            return ApprovalResult(approved=False, timed_out=True,
                                  reason="watchdog timeout")
        return decision["result"]

    # --------------------------------------------------------
    # Text-mode fallback (ask_user-style)
    # --------------------------------------------------------

    def _prompt_text_mode(self) -> ApprovalResult:
        """Headless fallback: print dialog + read stdin with watchdog."""
        import sys

        print(f"\n=== Approve tool `{self.tool_name}`? ===")
        if self.reason:
            print(f"Model reason: {self.reason}")
        for w in self.render_warnings():
            print(f"  {w}")
        if self.diff_html:
            print("[diff preview available — open in widget host to view]")
        print(f"Parameters (sanitised): {self._sanitised_params()}")
        print(f"Reply (a)pprove / (d)eny / (A)lways allow [60s timeout]:")

        # When stdin is not a TTY (notebook headless), default to deny so
        # we never silently auto-approve.
        if not sys.stdin.isatty():
            logging.warning(
                "PermissionDialog: stdin not a TTY; defaulting to DENY"
            )
            return ApprovalResult(approved=False, timed_out=True,
                                  reason="non-tty fallback")

        # Watchdog — readline doesn't natively support timeout; use a
        # signal-based timer where supported, else just block + record
        # the wall time.
        try:
            import select
            t_start = time.time()
            while True:
                if select.select([sys.stdin], [], [], 1)[0]:
                    line = sys.stdin.readline().strip()
                    if line in ("a", "approve", "y", "yes"):
                        return ApprovalResult(approved=True)
                    if line in ("A", "always"):
                        from runtime.config import CONFIG
                        if not hasattr(CONFIG, "_always_allowed"):
                            CONFIG._always_allowed = {}
                        CONFIG._always_allowed[self.tool_name] = True
                        return ApprovalResult(approved=True, always_allow=True,
                                              reason="text-mode Always-allow")
                    return ApprovalResult(approved=False, reason="user denied")
                if time.time() - t_start > self.timeout_seconds:
                    return ApprovalResult(approved=False, timed_out=True,
                                          reason="watchdog timeout")
        except (OSError, ValueError):
            # select.select unsupported (e.g. Windows non-socket).
            # Codex Block-C+ iter-1 finding #2 (HIGH) lock: a blocking
            # readline() with no timeout would hang indefinitely. Run
            # readline on a daemon thread + .join(timeout); if the
            # join times out, default to deny + timed_out.
            import threading

            answer: Dict[str, Any] = {"line": None}

            def _read():
                try:
                    answer["line"] = sys.stdin.readline()
                except Exception:
                    answer["line"] = None

            t = threading.Thread(target=_read, daemon=True)
            t.start()
            t.join(timeout=self.timeout_seconds)
            if t.is_alive():
                # Watchdog tripped — readline still blocked. Daemon
                # thread will be cleaned up on process exit.
                return ApprovalResult(approved=False, timed_out=True,
                                      reason="watchdog timeout (Windows fallback)")
            line = (answer["line"] or "").strip()
            if line in ("a", "approve", "y", "yes"):
                return ApprovalResult(approved=True)
            if line in ("A", "always"):
                from runtime.config import CONFIG
                if not hasattr(CONFIG, "_always_allowed"):
                    CONFIG._always_allowed = {}
                CONFIG._always_allowed[self.tool_name] = True
                return ApprovalResult(approved=True, always_allow=True)
            return ApprovalResult(approved=False, reason="user denied")

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _sanitised_params(self) -> Dict[str, Any]:
        """Truncate big strings; redact secret-looking keys."""
        out: Dict[str, Any] = {}
        for k, v in self.parameters.items():
            if any(s in k.lower() for s in (
                "password", "secret", "key", "token", "credential",
            )):
                out[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 200:
                out[k] = f"[{len(v)} chars]"
            else:
                out[k] = v
        return out


# ============================================================
# Rate limiter (Block C+ — port of v4 :8731-8740)
# ============================================================

class RateLimiter:
    """Sliding-window message rate limiter.

    100 user messages per 60s window per v4 default + per-session cap.
    Used at QueryEngine.run() entry. When rate exceeded, run() returns
    a clear error result without spending iteration budget.
    """

    def __init__(self, max_per_minute: int = 100, max_per_session: int = 1500):
        self.max_per_minute = max(1, int(max_per_minute))
        self.max_per_session = max(1, int(max_per_session))
        self._timestamps: List[float] = []
        self._session_count = 0

    def check(self) -> Optional[str]:
        """Return None if OK, or an error message if rate-limited.

        Caller must call this BEFORE any work that consumes budget.
        """
        now = time.time()
        # Drop stamps older than 60s.
        cutoff = now - 60.0
        self._timestamps = [t for t in self._timestamps if t >= cutoff]
        if len(self._timestamps) >= self.max_per_minute:
            wait = int(60 - (now - self._timestamps[0]))
            return (
                f"Rate limit hit: {self.max_per_minute} messages per minute. "
                f"Try again in ~{max(1, wait)}s."
            )
        if self._session_count >= self.max_per_session:
            return (
                f"Session message cap hit ({self.max_per_session}). "
                "Start a new session to continue."
            )
        self._timestamps.append(now)
        self._session_count += 1
        return None

    def reset(self) -> None:
        self._timestamps = []
        self._session_count = 0


__all__ = ["ApprovalResult", "PermissionDialog", "RateLimiter"]
