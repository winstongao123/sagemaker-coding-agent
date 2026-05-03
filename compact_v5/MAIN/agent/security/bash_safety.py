"""Block C C-9..C-14 — bash safety helpers.

Adapters of Runnable's `BashTool/commandSemantics.ts` (R1 #49) +
`BashTool/destructiveCommandWarning.ts` (R1 #50) +
`BashTool/bashCommandHelpers.ts` (R1 #53/54/55) + `BashTool/commentLabel.ts`
(R1 #48). Each helper is small and self-contained so `tools/bash.py`
can call them without growing.

Helpers:
  C-9  interpret_command_result   exit-code semantics (grep 1=no-match, etc.)
  C-10 destructive_command_warning rm -rf / git push --force / DROP TABLE / kubectl delete / terraform destroy
  C-11 has_cd_git_compound_with_bare_repo  cd into a bare git repo + git fsmonitor risk
  C-12 has_multiple_cd            `cd a && cd b && X` requires approval
  C-13 pipe_segment_permission_check  per-segment approval check
  C-14 extract_bash_comment_label  `# comment` → UI history label

PORT_LOG: see #061.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple


# ============================================================
# C-9 — Exit-code semantics
# ============================================================

# Commands whose non-zero exit-codes have well-known non-error meanings.
# Reporting them as "command failed" misleads the model.
_NONZERO_NON_ERROR_SEMANTICS: dict = {
    "grep": {1: "no match (not an error)"},
    "egrep": {1: "no match (not an error)"},
    "fgrep": {1: "no match (not an error)"},
    "rg": {1: "no match (not an error)"},
    "find": {1: "partial result (some paths inaccessible)"},
    "diff": {1: "files differ (not an error — diff worked)"},
    "cmp": {1: "files differ (not an error — cmp worked)"},
    "test": {1: "condition false (test worked)"},
}


def interpret_command_result(command: str, exit_code: int) -> Optional[str]:
    """Return a human-readable explanation for `command`'s exit code.

    None means "no special semantics — surface the raw exit code".
    Per Runnable BashTool/commandSemantics.ts:1-140 (R1 #49).
    """
    if exit_code == 0 or not command:
        return None
    # First token is the command name (after stripping env-vars / sudo).
    head = command.strip().split()
    if not head:
        return None
    # Skip env-var assignments: `FOO=bar grep ...`
    while head and "=" in head[0] and not head[0].startswith("="):
        head.pop(0)
    if not head:
        return None
    cmd_name = head[0].split("/")[-1]  # strip leading path
    semantics = _NONZERO_NON_ERROR_SEMANTICS.get(cmd_name)
    if semantics and exit_code in semantics:
        return semantics[exit_code]
    return None


# ============================================================
# C-10 — Destructive command warnings (catalog)
# ============================================================

_DESTRUCTIVE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\brm\s+-[rRf]+\b", re.IGNORECASE),
     "rm -rf / -fR — recursive force-delete"),
    (re.compile(r"\bgit\s+push\s+--force(-with-lease)?\b", re.IGNORECASE),
     "git push --force — overwrites remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "git reset --hard — discards local changes"),
    (re.compile(r"\bgit\s+clean\s+-[fdx]+\b", re.IGNORECASE),
     "git clean -fd / -fdx — deletes untracked files"),
    (re.compile(r"\bdrop\s+(table|database|schema)\b", re.IGNORECASE),
     "DROP TABLE / DATABASE / SCHEMA — irreversible SQL drop"),
    (re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
     "TRUNCATE TABLE — empties a SQL table"),
    (re.compile(r"\bkubectl\s+delete\b", re.IGNORECASE),
     "kubectl delete — removes Kubernetes resource"),
    (re.compile(r"\bterraform\s+destroy\b", re.IGNORECASE),
     "terraform destroy — tears down Terraform-managed infra"),
    (re.compile(r"\bdocker\s+(rm|rmi|system\s+prune)\b", re.IGNORECASE),
     "docker rm / rmi / system prune — destroys containers / images"),
    (re.compile(r"\bdd\s+if=.+\s+of=/dev/", re.IGNORECASE),
     "dd of=/dev/... — overwrites raw block device"),
    (re.compile(r":\s*\(\s*\)\s*\{\s*:\|:&\s*\}\s*;\s*:", re.IGNORECASE),
     "fork bomb"),
    (re.compile(r"\baws\s+s3\s+rb\s+.*--force\b", re.IGNORECASE),
     "aws s3 rb --force — deletes S3 bucket + contents"),
    (re.compile(r"\bredis-cli\s+(-[a-z]+\s+)*flushall\b", re.IGNORECASE),
     "redis-cli FLUSHALL — wipes every Redis db"),
]


def destructive_command_warning(command: str) -> Optional[str]:
    """Return the first destructive-pattern label, or None.

    Per Runnable BashTool/destructiveCommandWarning.ts (R1 #50).
    Used by the approval flow to surface a clear "this is dangerous"
    message before executing.
    """
    if not command:
        return None
    for pat, label in _DESTRUCTIVE_PATTERNS:
        if pat.search(command):
            return label
    return None


# ============================================================
# C-11 — cd into bare git repo + fsmonitor risk
# ============================================================

_CD_GIT_COMPOUND = re.compile(
    r"\bcd\s+([^\s&;|]+).*?\bgit\b", re.IGNORECASE
)


def has_cd_git_compound_with_bare_repo(command: str) -> bool:
    """True iff command does `cd <something> && git ...` AND the cd
    target is plausibly a bare repo (ends in .git).

    Bare repos with `core.fsmonitor` enabled launch a long-running
    helper that can survive shell exit + pin file handles. Per
    Runnable BashTool/bashCommandHelpers.ts:50-82 (R1 #53).
    """
    if not command:
        return False
    m = _CD_GIT_COMPOUND.search(command)
    if not m:
        return False
    target = m.group(1).strip().strip('"').strip("'")
    return target.endswith(".git") or target.endswith(".git/")


# ============================================================
# C-12 — Multiple cd detection
# ============================================================

_CD_TOKEN = re.compile(r"\bcd\s+", re.IGNORECASE)


def has_multiple_cd(command: str) -> bool:
    """True iff command contains 2+ `cd ` tokens (chained dir changes).

    Per Runnable BashTool/bashCommandHelpers.ts:32-47 (R1 #54). Multiple
    cd's confuse approval semantics — `cd a && cd b && rm X` looks like
    rm-relative-to-cwd but actually targets `b/X`.
    """
    if not command:
        return False
    return len(_CD_TOKEN.findall(command)) >= 2


# ============================================================
# C-13 — Pipe-segment permission check
# ============================================================

def split_pipe_segments(command: str) -> List[str]:
    """Split a command on top-level `|` (skipping `||`).

    Per Runnable BashTool/bashCommandHelpers.ts:84-156 (R1 #55). Each
    segment is then checked individually for destructive content so a
    pipeline like `harmless_cmd | rm -rf /` doesn't slip through.
    """
    if not command:
        return []
    out: List[str] = []
    cur: list = []
    i = 0
    n = len(command)
    in_single = False
    in_double = False
    while i < n:
        ch = command[i]
        if ch == "'" and not in_double:
            in_single = not in_single
            cur.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            cur.append(ch)
        elif ch == "|" and not in_single and not in_double:
            # Skip `||` (logical OR).
            if i + 1 < n and command[i + 1] == "|":
                cur.append("||")
                i += 2
                continue
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur:
        out.append("".join(cur).strip())
    return [s for s in out if s]


def pipe_segment_permission_check(command: str) -> List[str]:
    """Return destructive-warning labels for any pipe segment, or [].

    Joins per-segment results — useful when the approval flow wants to
    show "the second segment is destructive: <reason>".
    """
    warnings: List[str] = []
    for seg in split_pipe_segments(command):
        w = destructive_command_warning(seg)
        if w:
            warnings.append(w)
    return warnings


# ============================================================
# C-14 — Extract bash comment label
# ============================================================

_LEADING_COMMENT = re.compile(r"^\s*#\s*(.+?)\s*(?:$|\n)")


def extract_bash_comment_label(command: str) -> Optional[str]:
    """Return the leading `# comment` text, or None.

    Used by the UI history view to label long bash invocations with
    something the user wrote. Per Runnable BashTool/commentLabel.ts
    (R1 #48).
    """
    if not command:
        return None
    m = _LEADING_COMMENT.match(command)
    if not m:
        return None
    label = m.group(1).strip()
    return label if label else None


__all__ = [
    "interpret_command_result",
    "destructive_command_warning",
    "has_cd_git_compound_with_bare_repo",
    "has_multiple_cd",
    "split_pipe_segments",
    "pipe_segment_permission_check",
    "extract_bash_comment_label",
]
