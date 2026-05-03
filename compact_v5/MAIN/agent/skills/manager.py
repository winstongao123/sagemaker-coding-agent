"""V5 skills/manager.py — SkillManager (Phase 10, ADR-016).

PORT port of v4's `SkillManager` at `compact_v4/MAIN/agent/sagemaker_agent.py:2684`.
Adaptations for v5:
- `workspace` and `skills_dir` are constructor parameters (not pulled from
  globals) so tests can inject paths.
- Hermes filter (PS Issue #1): `discover_relevant(user_message, active_tools=None)`
  takes an optional active-tools set; if a skill declares `requires_tools` in
  its SKILL.md frontmatter, it's filtered out when those tools aren't active.
  Backwards-compatible: skills without the field are never filtered out by
  this mechanism.
- Self-patching surface (`propose_patch` / `list_proposals` / `apply_proposal` /
  `revert_skill`) is preserved verbatim. Tools using it gate on
  `CONFIG.enable_skill_patching=True` (default OFF — opt-in).

PORT_LOG: #025.

Phase 10 ships the 10 v4 production skills byte-for-byte:
    batch / clara / design / html / reflexion / report / review /
    security-review / simplify / verify.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# v4 listing-budget constants (sagemaker_agent.py:2660-2671) preserved verbatim.
SKILL_LISTING_BUDGET_PERCENT: float = 0.005     # 0.5% of context_max_tokens
SKILL_LISTING_HARD_CAP_TOKENS: int = 2000        # Safety upper bound
SKILL_LISTING_DESC_CAP: int = 250                # Per-skill description cap (chars)


# ============================================================
# SkillInfo dataclass
# ============================================================

@dataclass
class SkillInfo:
    """Parsed skill metadata. Same shape as v4 SkillInfo + Phase-10 addition
    of `requires_tools` (Hermes filter, optional) + Block I additions
    (paths / disable_model_invocation / enabled_when).
    """
    name: str
    description: str
    location: str          # full path to SKILL.md
    base_dir: str          # directory containing the skill
    triggers: Optional[List[str]] = None    # keywords for auto-discovery
    auto_trigger: bool = False              # explicit per-skill opt-in
    requires_tools: Optional[List[str]] = None   # Phase 10 Hermes filter (optional)
    # Block I-1 / R9 #1: fnmatch patterns for path-triggered auto-activation.
    # When the user edits a matching path, the skill auto-activates. None or
    # empty list means the skill is unconditional (the legacy behavior).
    paths: Optional[List[str]] = None
    # Block I-2 / R9 #3: when True, the skill is hidden from model-invocation
    # surfaces (skill_tool / discover_relevant) but remains user-invocable
    # via /skill use <name>. Useful for skills that should run only at human
    # request — e.g. /remember which the model shouldn't auto-trigger.
    disable_model_invocation: bool = False
    # Block I-3 / R9 #4: name of a CONFIG boolean attribute. If set, the
    # skill loads only when CONFIG.<enabled_when> is truthy. Lets a skill
    # be conditionally available behind an opt-in feature flag.
    enabled_when: Optional[str] = None


# ============================================================
# Helpers (token estimator + injection scanner)
# ============================================================

def _estimate_tokens(text: str) -> int:
    """Rough token estimator (4 chars/token, matches v4 Compactor.estimate_tokens
    semantics for short strings without pulling the full Compactor surface)."""
    return max(1, len(text) // 4)


def _scan_for_prompt_injection(content: str, source_label: str) -> List[str]:
    """Defensive scan for prompt-injection markers in skill content. Returns
    a list of warning strings (advisory). Same advisory contract as v4
    (sagemaker_agent.py uses _scan_for_prompt_injection at line 2802).

    Block C (Codex iter-1 finding #1) lock: delegates to the v4-native
    12-pattern scanner at security/injection_scanner.py (ADR-020 0-10
    remap). Falls back to the local 5-marker contract if the security
    helper is unavailable so skill loading never breaks on import error.
    """
    try:
        from security.injection_scanner import scan_for_prompt_injection
        prefixed = scan_for_prompt_injection(content, source_label)
        # Wrap each hit with the legacy `[skill-injection-scan]` prefix so
        # downstream callers (Hermes filter advisory, /skills inspector)
        # still recognise the format.
        return [f"[skill-injection-scan] {w} (advisory)" for w in prefixed]
    except Exception:
        # Conservative fallback to the 5-marker contract.
        warnings: List[str] = []
        markers = (
            "ignore previous instructions",
            "<system>",
            "</system>",
            "you are now",
            "disregard the above",
        )
        low = (content or "").lower()
        for m in markers:
            if m in low:
                warnings.append(
                    f"[skill-injection-scan] '{source_label}' contains marker '{m}' "
                    "(advisory; review skill content for prompt injection)."
                )
        return warnings


# ============================================================
# SkillManager
# ============================================================

class SkillManager:
    """Multi-directory skill loader. Discovers **/SKILL.md with YAML frontmatter."""

    PROPOSED_DIR_NAME = ".proposed"

    def __init__(
        self,
        workspace: str,
        skills_dir: str = "./skills",
        enable_auto_trigger: bool = False,
    ):
        """Construct a SkillManager.

        Args:
            workspace: working directory; used as the anchor for legacy
                `.agent/skills` and `.claude/skills` discovery.
            skills_dir: primary skills directory (resolved against `workspace`
                if relative).
            enable_auto_trigger: global gate for `discover_relevant`. v4.9.6
                default-OFF preserved; passing True opts in.
        """
        self.workspace = Path(workspace).resolve()
        if os.path.isabs(skills_dir):
            self.skills_dir = Path(skills_dir).resolve()
        else:
            self.skills_dir = (self.workspace / skills_dir).resolve()
        os.makedirs(self.skills_dir, exist_ok=True)
        self._cache: Dict[str, SkillInfo] = {}
        self.active_skill: Optional[str] = None
        self._pending_activations: List[str] = []
        self._pending_lock = threading.Lock()
        self._enable_auto_trigger = bool(enable_auto_trigger)

    # ------------------------------------------------------------
    # Frontmatter parser (v4 verbatim)
    # ------------------------------------------------------------

    def _parse_frontmatter(self, text: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter from markdown. Returns (metadata, content).

        Codex Phase-10 finding (HIGH): the v4-style line-split parser only
        understood scalar `key: value` lines. v5 also accepts YAML list form:

            requires_tools:
              - bash
              - python_exec

        Stored as a list-of-strings in the metadata dict (not a CSV string).
        Block scalar / multiline / quoted-string forms remain unsupported —
        documented in the SkillInfo `requires_tools` field's docstring as
        "use CSV scalar OR YAML list dash-form."
        """
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                meta: Dict[str, Any] = {}
                fm_lines = parts[1].strip().splitlines()
                i = 0
                while i < len(fm_lines):
                    line = fm_lines[i]
                    if ":" not in line:
                        i += 1
                        continue
                    key, _, val = line.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if val == "":
                        # Possibly a YAML list — peek ahead for `  - item` lines.
                        items: List[str] = []
                        j = i + 1
                        while j < len(fm_lines):
                            nxt = fm_lines[j]
                            stripped = nxt.lstrip()
                            if stripped.startswith("- "):
                                items.append(stripped[2:].strip())
                                j += 1
                                continue
                            if not stripped:
                                j += 1
                                continue
                            # Not a list item and not blank — back to scalar parse
                            break
                        if items:
                            meta[key] = items
                            i = j
                            continue
                    meta[key] = val
                    i += 1
                return meta, parts[2].strip()
        # Fallback: first non-empty line as description
        lines = text.strip().splitlines()
        first = next((ln.strip().lstrip("# ") for ln in lines if ln.strip()), "")
        return {"description": first[:120]}, text

    @staticmethod
    def _split_csv_field(raw: Any) -> Optional[List[str]]:
        """Normalize a frontmatter list-shaped field to List[str] or None.

        Codex Phase-10 finding (HIGH): accept both forms — CSV scalar
        (`requires_tools: bash, python_exec`) and YAML list-of-strings (already
        decoded by `_parse_frontmatter`). Returns None for empty / missing.
        """
        if raw is None:
            return None
        if isinstance(raw, list):
            cleaned = [str(t).strip() for t in raw if str(t).strip()]
            return cleaned or None
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                return None
            return [t.strip() for t in s.split(",") if t.strip()]
        # Anything else — coerce to str then split
        s = str(raw).strip()
        if not s:
            return None
        return [t.strip() for t in s.split(",") if t.strip()]

    # ------------------------------------------------------------
    # discover() — verbatim from v4 + Phase 10 requires_tools parsing
    # ------------------------------------------------------------

    def discover(self) -> Dict[str, SkillInfo]:
        """Scan for **/SKILL.md files and legacy *.md files.

        Block I-4 / R9 #23: realpath-dedup. Skills loaded via symlink or
        duplicate parent paths are de-duplicated by their resolved real
        path so the same SKILL.md isn't loaded twice (which previously
        produced double tool-listing entries).
        """
        self._cache.clear()
        # Block I-4 lock: track real paths we've already seen this discovery
        # cycle. First-wins ordering matches Runnable's
        # `seenFileIds` Map at loadSkillsDir.ts:736-763.
        seen_realpaths: Set[str] = set()
        search_dirs = [self.skills_dir]
        for sub in (".agent/skills", ".claude/skills"):
            d = self.workspace / sub
            if d.is_dir():
                search_dirs.append(d)

        for search_dir in search_dirs:
            for fp in sorted(search_dir.rglob("SKILL.md")):
                try:
                    real = os.path.realpath(str(fp))
                    if real in seen_realpaths:
                        logging.debug(
                            f"[skill-dedup] skipping '{fp}' (same realpath "
                            f"as already-loaded skill)"
                        )
                        continue
                    seen_realpaths.add(real)

                    text = fp.read_text(encoding="utf-8", errors="ignore")
                    meta, content = self._parse_frontmatter(text)
                    name = meta.get("name", fp.parent.name)
                    desc = meta.get("description", "")
                    if not desc and content:
                        for line in content.split("\n"):
                            line = line.strip()
                            if line.startswith("#"):
                                desc = line.lstrip("#").strip()
                                break
                    auto_trigger = str(meta.get("auto_trigger", "false")).strip().lower() == "true"
                    # triggers + requires_tools both accept CSV scalar OR YAML list
                    raw_triggers = meta.get("triggers")
                    triggers_list = self._split_csv_field(raw_triggers) or []
                    triggers = (
                        [t.lower() for t in triggers_list]
                        if (triggers_list and auto_trigger) else None
                    )
                    requires_tools = self._split_csv_field(meta.get("requires_tools"))
                    # Block I-1 / R9 #1: paths frontmatter. Strip trailing
                    # /** (Runnable's transform: a directory pattern matches
                    # both itself and its descendants). All-`**` patterns
                    # collapse to None so the skill is unconditional.
                    raw_paths = self._split_csv_field(meta.get("paths"))
                    paths: Optional[List[str]] = None
                    if raw_paths:
                        normalized = []
                        for p in raw_paths:
                            if p.endswith("/**"):
                                p = p[:-3]
                            if p:
                                normalized.append(p)
                        if normalized and not all(p == "**" for p in normalized):
                            paths = normalized
                    # Block I-2 / R9 #3
                    disable_model_invocation = (
                        str(meta.get("disable_model_invocation", "false"))
                        .strip().lower() == "true"
                    )
                    # Block I-3 / R9 #4
                    enabled_when_raw = meta.get("enabled_when", "")
                    enabled_when = (
                        str(enabled_when_raw).strip() if enabled_when_raw else None
                    )

                    # Block I-3: skip the skill entirely when its
                    # enabled_when CONFIG flag is falsy. Loading is
                    # conditional on the gate, not just visibility.
                    if enabled_when and not self._enabled_when_truthy(enabled_when):
                        logging.debug(
                            f"[skill-gate] skipping '{name}' "
                            f"(enabled_when={enabled_when} is falsy)"
                        )
                        continue

                    if desc and not desc.lower().lstrip().startswith("use when"):
                        logging.debug(
                            f"[CSO-CHECK] skill '{name}' description does not start with 'Use when'"
                        )

                    self._cache[name] = SkillInfo(
                        name=name,
                        description=desc,
                        location=str(fp),
                        base_dir=str(fp.parent),
                        triggers=triggers,
                        auto_trigger=auto_trigger,
                        requires_tools=requires_tools,
                        paths=paths,
                        disable_model_invocation=disable_model_invocation,
                        enabled_when=enabled_when,
                    )
                except Exception:
                    continue

            # Legacy flat *.md fallback (skills_dir only)
            if search_dir == self.skills_dir:
                for fp in sorted(search_dir.glob("*.md")):
                    if fp.name == "SKILL.md":
                        continue
                    try:
                        text = fp.read_text(encoding="utf-8", errors="ignore")
                        meta, content = self._parse_frontmatter(text)
                        name = meta.get("name", fp.stem)
                        desc = meta.get("description", "")
                        if name not in self._cache:
                            self._cache[name] = SkillInfo(
                                name=name,
                                description=desc,
                                location=str(fp),
                                base_dir=str(fp.parent),
                            )
                    except Exception:
                        continue
        return self._cache

    # ------------------------------------------------------------
    # Public read surface
    # ------------------------------------------------------------

    def list_skills(self) -> List[Dict]:
        if not self._cache:
            self.discover()
        return [
            {"name": s.name, "description": s.description, "path": s.location}
            for s in self._cache.values()
        ]

    def read_skill(self, name: str, max_chars: int = 12000) -> Tuple[bool, str]:
        if not self._cache:
            self.discover()
        skill = self._cache.get(name)
        if not skill:
            available = ", ".join(self._cache.keys()) if self._cache else "none"
            return False, f"Skill '{name}' not found. Available: {available}"
        try:
            text = Path(skill.location).read_text(encoding="utf-8", errors="ignore")
            _, content = self._parse_frontmatter(text)
            for w in _scan_for_prompt_injection(content, f"skill:{name}"):
                logging.warning(w)
            return True, content[:max_chars]
        except Exception as e:
            return False, f"Failed reading skill: {e}"

    def get_active_skill_prompt(self, session_id: str = "") -> str:
        """Return the active skill's body for prompt injection.

        Codex iter-1 finding #3 fix: I-6 ${CLAUDE_SKILL_DIR} /
        ${CLAUDE_SESSION_ID} substitution is now applied here so the
        prompt actually carries the resolved values, not literal vars.
        Caller (query_engine) passes its session_id; an empty string
        leaves ${CLAUDE_SESSION_ID} in place (deliberate — see
        substitute_skill_vars docstring).
        """
        if not self.active_skill:
            return ""
        ok, content = self.read_skill(self.active_skill)
        if not ok:
            return ""
        skill = self._cache.get(self.active_skill)
        # Apply Block I-6 substitution.
        content = self.substitute_skill_vars(
            content, self.active_skill, session_id=session_id,
        )
        return (
            f"\n\n## Active Skill: {self.active_skill}\n"
            f"Base directory: {skill.base_dir if skill else 'unknown'}\n\n"
            f"{content}"
        )

    def activate(self, name: str) -> Tuple[bool, str]:
        """Activate a skill so its body is injected into subsequent prompts.

        Returns (ok, message). Lock-tested: an unknown name returns ok=False
        with the available list."""
        if not self._cache:
            self.discover()
        if name not in self._cache:
            available = ", ".join(sorted(self._cache.keys())) if self._cache else "none"
            return False, f"Skill '{name}' not found. Available: {available}"
        with self._pending_lock:
            self.active_skill = name
            self._pending_activations.append(name)
        return True, f"Skill '{name}' activated."

    def deactivate(self) -> None:
        with self._pending_lock:
            self.active_skill = None

    # ------------------------------------------------------------
    # Block I-3 — enabled_when CONFIG-flag predicate
    # ------------------------------------------------------------

    @staticmethod
    def _enabled_when_truthy(attr: str) -> bool:
        """Return True iff CONFIG.<attr> is truthy. Best-effort: when
        CONFIG can't be imported (test isolation, partial env), default
        to NOT loading the skill (fail-closed) so a typo in the flag
        name doesn't accidentally enable an opt-in skill.
        """
        try:
            from runtime.config import CONFIG as _CFG
            return bool(getattr(_CFG, attr, False))
        except Exception:
            return False

    # ------------------------------------------------------------
    # Block I-1 / I-5 — path-triggered auto-activation
    # ------------------------------------------------------------

    def activate_for_path(self, file_path: str) -> List[str]:
        """When the user edits/writes `file_path`, auto-activate any skill
        whose `paths` frontmatter matches via fnmatch. Skills already
        active are skipped (no-op).

        Returns the list of newly-activated skill names. Caller (edit/write
        tool) can surface this to the user.
        """
        import fnmatch
        if not self._cache:
            self.discover()
        # Normalize the path: relative to workspace if possible, else basename.
        try:
            normalized = str(Path(file_path))
            try:
                normalized = str(Path(file_path).resolve().relative_to(self.workspace))
            except Exception:
                normalized = str(Path(file_path))
        except Exception:
            normalized = file_path
        # Compare with both the full and basename forms; patterns are
        # typically `*.py` or `src/*` — fnmatch handles both.
        candidates = {normalized, os.path.basename(normalized)}
        # Replace backslash → forward-slash for cross-platform fnmatch.
        candidates = {c.replace("\\", "/") for c in candidates}

        activated: List[str] = []
        for name, skill in self._cache.items():
            if not skill.paths:
                continue
            if name == self.active_skill:
                continue
            for pattern in skill.paths:
                pat_norm = pattern.replace("\\", "/")
                # Codex iter-1 finding #1 fix: stripped directory pattern
                # ("src" from "src/**") must match descendants. fnmatch alone
                # doesn't recognize a directory root — augment with explicit
                # equality + prefix-with-separator match.
                root = pat_norm.rstrip("/")
                matched = any(
                    fnmatch.fnmatch(c, pat_norm)
                    or c == root
                    or c.startswith(root + "/")
                    for c in candidates
                )
                if matched:
                    with self._pending_lock:
                        self.active_skill = name
                        self._pending_activations.append(name)
                    activated.append(name)
                    logging.info(
                        f"[skill-paths] auto-activated '{name}' "
                        f"on edit of '{file_path}' (pattern={pattern!r})"
                    )
                    # Codex iter-1 finding #4 fix: first-match-wins per
                    # ADR-029 §1. v5 has a single active_skill; iterating
                    # all skills lets a later match silently overwrite
                    # the first. Return after the first activation so the
                    # documented contract holds.
                    return activated
        return activated

    # ------------------------------------------------------------
    # Block I-2 — model-vs-user visibility split
    # ------------------------------------------------------------

    def list_model_invocable(self) -> List[Dict]:
        """Return only skills the model is allowed to invoke. Hides any
        skill with `disable_model_invocation: true` (Block I-2 / R9 #3).
        Use this for the skill_tool LLM tool description.
        """
        if not self._cache:
            self.discover()
        return [
            {"name": s.name, "description": s.description, "path": s.location}
            for s in self._cache.values()
            if not s.disable_model_invocation
        ]

    def list_user_invocable(self) -> List[Dict]:
        """All skills are user-invocable by default. v5 has no per-skill
        user-disable knob (Runnable's `userInvocable: false` is unused in
        the bundled set); this method exists so callers don't have to know.
        """
        return self.list_skills()

    # ------------------------------------------------------------
    # Block I — fuzzy name resolution (Hermes pattern)
    # ------------------------------------------------------------

    def resolve_name(self, query: str) -> Optional[str]:
        """Resolve a query to a canonical skill name.

        Resolution order (Hermes run_agent.py:4685-4724 fast-path-then-fuzzy):
        1. Exact directory name match.
        2. Case-insensitive directory or metadata `name:` match.
        3. Hermes fuzzy: difflib.get_close_matches with cutoff=0.7.

        Returns the canonical key into self._cache, or None if no match
        crosses the cutoff. Never raises — callers can fall back to
        printing the available list.
        """
        from difflib import get_close_matches

        if not self._cache:
            self.discover()
        if not query:
            return None
        if query in self._cache:
            return query

        # Build the candidate pool: directory names + metadata names from
        # SkillInfo. Metadata `name:` field is what self._cache is keyed
        # by, so the keys ARE the metadata names.
        canonical_names = list(self._cache.keys())
        # Also include directory basenames in case metadata name differs
        # from directory name (e.g. directory=clara-review, name=Clara).
        dir_names = {os.path.basename(s.base_dir): n for n, s in self._cache.items()}

        # 2a. exact case-insensitive match against canonical or dir name.
        ql = query.lower()
        for name in canonical_names:
            if name.lower() == ql:
                return name
        for dname, canonical in dir_names.items():
            if dname.lower() == ql:
                return canonical

        # 2b. Hermes-style normalization: strip "skill"/"-skill"/"_skill" suffix.
        suffixes = ("_skill", "-skill", "skill")
        for suffix in suffixes:
            if ql.endswith(suffix):
                base = ql[: -len(suffix)].rstrip("_-")
                for name in canonical_names:
                    if name.lower() == base:
                        return name
                for dname, canonical in dir_names.items():
                    if dname.lower() == base:
                        return canonical
                break

        # 3. Fuzzy fallback (difflib.get_close_matches cutoff=0.7).
        all_names_lower = {n.lower(): n for n in canonical_names}
        all_names_lower.update({d.lower(): n for d, n in dir_names.items()})
        matches = get_close_matches(ql, list(all_names_lower.keys()), n=1, cutoff=0.7)
        if matches:
            return all_names_lower[matches[0]]
        return None

    # ------------------------------------------------------------
    # Block I-6 — ${CLAUDE_SKILL_DIR} / ${CLAUDE_SESSION_ID} substitution
    # ------------------------------------------------------------

    def substitute_skill_vars(
        self,
        content: str,
        skill_name: str,
        session_id: str = "",
    ) -> str:
        """Replace ${CLAUDE_SKILL_DIR} and ${CLAUDE_SESSION_ID} in skill content.

        Per Runnable loadSkillsDir.ts:356-369, ${CLAUDE_SKILL_DIR} resolves
        to the skill's own base_dir (forward-slash on Windows so callers can
        reference bundled scripts safely) and ${CLAUDE_SESSION_ID} resolves
        to the supplied session_id.

        Block I-6 SECURITY note: v5 does NOT execute inline shell commands
        from skill markdown bodies (Runnable's `executeShellCommandsInPrompt`
        is intentionally NOT ported — constraint #10 + #9 keep the skill
        content as text-only context). Variable substitution is therefore
        safe; there is no path through which a substituted value reaches
        a shell.
        """
        if not content:
            return content
        skill = self._cache.get(skill_name)
        if skill is not None:
            base_dir = skill.base_dir
            # Cross-platform forward-slash.
            base_dir_fwd = base_dir.replace("\\", "/")
            content = content.replace("${CLAUDE_SKILL_DIR}", base_dir_fwd)
        if session_id:
            content = content.replace("${CLAUDE_SESSION_ID}", session_id)
        return content

    # ------------------------------------------------------------
    # discover_relevant() — auto-trigger with Hermes filter (PS Issue #1)
    # ------------------------------------------------------------

    def discover_relevant(
        self,
        user_message: str,
        active_tools: Optional[Iterable[str]] = None,
    ) -> List[str]:
        """Auto-discover skills relevant to the user's message.

        Phase-10 addition: when `active_tools` is provided, skills declaring
        `requires_tools` are filtered out unless every required tool is in
        `active_tools` (Hermes filter, PS Issue #1). Skills WITHOUT
        `requires_tools` are never filtered out by this mechanism — preserves
        backwards compatibility with the 10 v4 skills.
        """
        if not self._cache:
            self.discover()
        if not self._enable_auto_trigger:
            return []

        msg_lower = user_message.lower()
        active_set: Optional[Set[str]] = (
            set(active_tools) if active_tools is not None else None
        )

        relevant: List[str] = []
        for name, skill in self._cache.items():
            if name == self.active_skill:
                continue
            # Codex iter-1 finding #2 fix: disable_model_invocation
            # must hide the skill from this model-facing surface too.
            # Without this filter, a `remember`-style skill that opted
            # out of model invocation would still be auto-suggested by
            # discover_relevant when its triggers fired.
            if skill.disable_model_invocation:
                continue
            if not skill.triggers:
                continue
            if not any(trigger in msg_lower for trigger in skill.triggers):
                continue
            # Hermes filter
            if (
                active_set is not None
                and skill.requires_tools
                and not all(t in active_set for t in skill.requires_tools)
            ):
                logging.debug(
                    f"[hermes-filter] skill '{name}' filtered: "
                    f"requires {skill.requires_tools}, active set lacks "
                    f"{[t for t in skill.requires_tools if t not in active_set]}"
                )
                continue
            relevant.append(name)
        return relevant

    # ------------------------------------------------------------
    # list_for_prompt() — token-budgeted listing for tool description
    # ------------------------------------------------------------

    def list_for_prompt(self, budget_tokens: int = 0, context_max_tokens: int = 200000) -> str:
        """Compact skill listing for LLM tool description (token-efficient).

        v4 verbatim with `context_max_tokens` taken as a parameter (v4 read
        from CONFIG)."""
        if not self._cache:
            self.discover()
        if not self._cache:
            return ""
        if budget_tokens <= 0:
            ctx_max = context_max_tokens or 200000
            budget_tokens = max(1, int(ctx_max * SKILL_LISTING_BUDGET_PERCENT))
        budget_tokens = min(budget_tokens, SKILL_LISTING_HARD_CAP_TOKENS)

        names = list(self._cache.keys())
        n_total = len(names)
        hint_reserve = _estimate_tokens(f"...(+{n_total} more), ")

        out_names: List[str] = []
        used = _estimate_tokens("Available: ")
        truncated = False
        for name in names:
            cost = _estimate_tokens(name + ", ")
            if used + cost + hint_reserve > budget_tokens:
                truncated = True
                break
            out_names.append(name)
            used += cost

        if truncated:
            omitted = n_total - len(out_names)
            if not out_names:
                hint_only = f"Available: ...(+{omitted} more)"
                return hint_only if _estimate_tokens(hint_only) <= budget_tokens else ""
            out_names.append(f"...(+{omitted} more)")

        return "Available: " + ", ".join(out_names)

    # ============================================================
    # Self-patching surface (v4.9.5 verbatim — opt-in via CONFIG flag)
    # ============================================================

    def _proposed_dir(self, skill_name: str):
        skill = self._cache.get(skill_name)
        if not skill:
            return None
        return Path(skill.base_dir) / self.PROPOSED_DIR_NAME

    def propose_patch(self, name: str, reason: str, new_content: str) -> Tuple[bool, str]:
        """Write a proposed patch to skills/<name>/.proposed/<ts>.md.

        NEVER touches live SKILL.md. Returns (success, path_or_message).
        v4 verbatim — same 8 safety rails (propose-not-apply, .proposed/ dir,
        timestamped filename, metadata header with reason, audit-friendly
        wrapping)."""
        if not self._cache:
            self.discover()
        skill = self._cache.get(name)
        if not skill:
            available = ", ".join(sorted(self._cache.keys())) if self._cache else "none"
            return False, f"Skill not found: {name}. Available: {available}"
        if not (reason or "").strip():
            return False, "Reason is required (one sentence explaining why this patch helps)."
        if not (new_content or "").strip():
            return False, "new_content is required (the full replacement SKILL.md body, not a diff)."

        proposed_dir = self._proposed_dir(name)
        if proposed_dir is None:
            return False, f"Cannot resolve .proposed/ for skill '{name}'."
        try:
            proposed_dir.mkdir(parents=True, exist_ok=True)
            # Codex Phase-10 finding (HIGH): second-granularity timestamps can
            # collide if two proposals fire in the same second. Add a short
            # uuid hex suffix so concurrent / rapid proposals never overwrite.
            import uuid
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_unique = f"{ts}_{uuid.uuid4().hex[:6]}"
            proposed_path = proposed_dir / f"{ts_unique}.md"
            wrapped = (
                f"<!-- proposed_at: {ts}\n"
                f"     skill: {name}\n"
                f"     reason: {reason.strip()}\n"
                f"-->\n"
                f"{new_content}"
            )
            proposed_path.write_text(wrapped, encoding="utf-8")
            # Best-effort audit log (Codex Phase-10 finding HIGH on safety
            # rails). Falls back to a logging.info line when AuditLogger
            # isn't wired (Phase 11 UX is the primary AuditLogger consumer
            # — Phase 10 best-efforts so the rail isn't entirely missing).
            try:
                from runtime.audit import AuditLogger  # noqa: F401
                logging.info(
                    "[skill-audit] propose name=%s ts=%s reason=%r path=%s",
                    name, ts_unique, reason.strip(), str(proposed_path),
                )
            except Exception:
                logging.info(
                    "[skill-audit-fallback] propose name=%s ts=%s",
                    name, ts_unique,
                )
            return True, str(proposed_path)
        except Exception as e:
            return False, f"Failed to write proposal: {e}"

    def list_proposals(self) -> List[Dict]:
        if not self._cache:
            self.discover()
        out: List[Dict] = []
        for name, skill in self._cache.items():
            pdir = Path(skill.base_dir) / self.PROPOSED_DIR_NAME
            if not pdir.is_dir():
                continue
            for fp in sorted(pdir.glob("*.md")):
                reason = ""
                try:
                    head = fp.read_text(encoding="utf-8", errors="ignore").splitlines()[:5]
                    for line in head:
                        if "reason:" in line.lower():
                            reason = line.split("reason:", 1)[1].strip()
                            if reason.endswith("-->"):
                                reason = reason[:-3].strip()
                            break
                except Exception:
                    pass
                out.append({
                    "skill": name,
                    "ts": fp.stem,
                    "path": str(fp),
                    "reason": reason,
                })
        return out

    def get_latest_proposal(self, name: str) -> Optional[Dict]:
        proposals = [p for p in self.list_proposals() if p["skill"] == name]
        if not proposals:
            return None
        proposals.sort(key=lambda p: p["ts"])
        return proposals[-1]

    def apply_proposal(self, name: str) -> Tuple[bool, str]:
        """Apply the LATEST pending proposal for skill `name`.

        Snapshot+overwrite live SKILL.md, delete proposal file. Caller (Phase 11
        UX) is expected to gate on user approval before calling this."""
        if not self._cache:
            self.discover()
        skill = self._cache.get(name)
        if not skill:
            return False, f"Skill not found: {name}"
        proposal = self.get_latest_proposal(name)
        if not proposal:
            return False, f"No pending proposals for skill '{name}'."
        live_path = Path(skill.location)
        proposed_path = Path(proposal["path"])
        try:
            proposed_text = proposed_path.read_text(encoding="utf-8", errors="ignore")
            stripped = proposed_text
            if stripped.lstrip().startswith("<!--"):
                end = stripped.find("-->")
                if end != -1:
                    stripped = stripped[end + 3:].lstrip()
            # Codex Phase-10 finding (HIGH): the v4.9.5 contract advertises
            # 8 safety rails including (4) snapshot before overwrite and
            # (5) audit log on apply. v5 Phase-10 honors both as best-effort:
            # if runtime/snapshot.SnapshotManager is wired (Phase 11 UX),
            # we call it; otherwise we copy the live file to a sibling
            # `.skill_backup_<ts>` so the change is locally reversible.
            import shutil
            from datetime import datetime as _dt
            backup_path = None
            try:
                from runtime.snapshot import SnapshotManager  # noqa: F401
                # Phase 11 UX is expected to inject a SnapshotManager
                # singleton; Phase 10 doesn't — fall through to local backup.
                raise NotImplementedError("snapshot singleton not wired in Phase 10")
            except Exception:
                try:
                    bts = _dt.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = live_path.with_name(
                        f"{live_path.name}.skill_backup_{bts}"
                    )
                    shutil.copy2(str(live_path), str(backup_path))
                except Exception:
                    backup_path = None  # backup best-effort; don't block apply

            live_path.write_text(stripped, encoding="utf-8")
            self._cache.clear()
            self.discover()
            try:
                proposed_path.unlink()
            except Exception:
                pass
            # Audit log (Codex Phase-10 finding HIGH on safety rails)
            logging.info(
                "[skill-audit] apply name=%s ts=%s backup=%s",
                name, proposal['ts'], str(backup_path) if backup_path else "(none)",
            )
            return True, f"Applied proposal for '{name}' from {proposal['ts']}."
        except Exception as e:
            return False, f"Apply failed: {e}"
