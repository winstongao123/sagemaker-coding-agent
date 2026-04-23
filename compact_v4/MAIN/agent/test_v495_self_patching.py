"""
V4.9.5 tests — self-patching skills with safety rails (hermes pattern, human-in-loop).

Covers:
  1. CONFIG.enable_skill_patching defaults to False (opt-out by default)
  2. SkillManager.propose_patch writes to .proposed/<ts>.md, never touches live SKILL.md
  3. propose_patch validates: skill exists, reason non-empty, new_content non-empty
  4. list_proposals discovers across all skills + parses reason from header
  5. get_latest_proposal returns the most recent ts when multiple stack
  6. apply_proposal writes new_content to live, deletes proposal, audit-logs
  7. apply_proposal strips the metadata header before writing live
  8. reject_proposal deletes ALL pending proposals for a skill
  9. tool_skill_propose_patch returns no-op message when CONFIG.enable_skill_patching = False
 10. tool_skill_propose_patch end-to-end when enabled
 11. Audit log file gets a JSONL line per propose / apply / reject

Run: python test_v495_self_patching.py
"""

from __future__ import annotations
import os
import sys
import json
import logging
import tempfile
import traceback
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa  # type: ignore

logging.disable(logging.WARNING)

RESULTS: List[Tuple[str, bool, str]] = []


def _run(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"  ok  {name}")
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
        print(f"  FAIL {name}")
        print(f"       AssertionError: {e}")
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  FAIL {name}")
        print(f"       {type(e).__name__}: {e}")
        traceback.print_exc()


def _write_skill(dir_path, name, body="initial body\n"):
    skill_dir = os.path.join(dir_path, name)
    os.makedirs(skill_dir, exist_ok=True)
    fp = os.path.join(skill_dir, "SKILL.md")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(
            "---\n"
            f"name: {name}\n"
            + ("descrip" + "tion") + f": Use when test fixture for {name}\n"
            "auto_trigger: false\n"
            "---\n\n"
            f"# {name}\n{body}"
        )
    return fp


def _fresh_manager(root):
    m = sa.SkillManager(workspace=root, skills_dir=root)
    m.discover()
    return m


# ============================================================
# Config flag default
# ============================================================

def test_config_flag_defaults_off():
    assert sa.CONFIG.enable_skill_patching is False, (
        "enable_skill_patching MUST default to False (opt-in only)"
    )


# ============================================================
# SkillManager.propose_patch
# ============================================================

def test_propose_patch_writes_to_proposed_dir():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "alpha")
        m = _fresh_manager(tmp)
        ok, msg = m.propose_patch("alpha", "test reason", "new body content here\nwith multiple lines\n")
        assert ok, f"propose should succeed: {msg}"
        assert ".proposed" in msg, f"path should be in .proposed dir: {msg}"
        assert os.path.isfile(msg), f"proposal file should exist: {msg}"


def test_propose_patch_does_not_modify_live_skill():
    with tempfile.TemporaryDirectory() as tmp:
        live = _write_skill(tmp, "beta", body="ORIGINAL CONTENT\n")
        m = _fresh_manager(tmp)
        original = open(live, encoding="utf-8").read()
        m.propose_patch("beta", "reason", "TOTALLY DIFFERENT CONTENT")
        after = open(live, encoding="utf-8").read()
        assert after == original, "live SKILL.md must NOT change when proposing"


def test_propose_patch_rejects_unknown_skill():
    with tempfile.TemporaryDirectory() as tmp:
        m = _fresh_manager(tmp)
        ok, msg = m.propose_patch("nonexistent", "r", "c")
        assert not ok and "not found" in msg.lower()


def test_propose_patch_rejects_empty_reason():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "gamma")
        m = _fresh_manager(tmp)
        ok, msg = m.propose_patch("gamma", "", "content")
        assert not ok and "reason" in msg.lower()


def test_propose_patch_rejects_empty_content():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "delta")
        m = _fresh_manager(tmp)
        ok, msg = m.propose_patch("delta", "reason", "")
        assert not ok and "new_content" in msg.lower()


def test_propose_patch_writes_metadata_header():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "epsilon")
        m = _fresh_manager(tmp)
        ok, path = m.propose_patch("epsilon", "fixed dpi default", "new content body")
        assert ok
        text = open(path, encoding="utf-8").read()
        assert "<!--" in text and "-->" in text, "should include metadata header"
        assert "fixed dpi default" in text, "reason should be in header"
        assert "new content body" in text, "new_content should be in body"


# ============================================================
# list_proposals + get_latest_proposal
# ============================================================

def test_list_proposals_empty_when_none_pending():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "zeta")
        m = _fresh_manager(tmp)
        assert m.list_proposals() == []


def test_list_proposals_includes_reason_from_header():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "eta")
        m = _fresh_manager(tmp)
        m.propose_patch("eta", "reason for patch X", "body")
        props = m.list_proposals()
        assert len(props) == 1
        assert props[0]["skill"] == "eta"
        assert "reason for patch X" in props[0]["reason"]


def test_get_latest_proposal_returns_most_recent_ts():
    """When multiple proposals stack, get_latest must return the most recent by ts."""
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "theta")
        m = _fresh_manager(tmp)
        ok1, p1 = m.propose_patch("theta", "first", "body 1")
        assert ok1
        _t.sleep(1.05)  # ensure different timestamp (granularity is seconds)
        ok2, p2 = m.propose_patch("theta", "second", "body 2")
        assert ok2
        latest = m.get_latest_proposal("theta")
        assert latest is not None
        assert latest["path"] == p2, "latest should be the SECOND (newer) proposal"


# ============================================================
# apply_proposal
# ============================================================

def test_apply_proposal_writes_to_live_skill():
    with tempfile.TemporaryDirectory() as tmp:
        live = _write_skill(tmp, "iota", body="OLD\n")
        m = _fresh_manager(tmp)
        m.propose_patch("iota", "swap", "---\nname: iota\n---\n\n# iota\nNEW BODY\n")
        ok, msg = m.apply_proposal("iota")
        assert ok, msg
        new_text = open(live, encoding="utf-8").read()
        assert "NEW BODY" in new_text


def test_apply_proposal_strips_metadata_header():
    """The HTML comment header in the proposal file must NOT land in live SKILL.md."""
    with tempfile.TemporaryDirectory() as tmp:
        live = _write_skill(tmp, "kappa")
        m = _fresh_manager(tmp)
        m.propose_patch("kappa", "test", "---\nname: kappa\n---\n\nclean body content\n")
        ok, _ = m.apply_proposal("kappa")
        assert ok
        new_text = open(live, encoding="utf-8").read()
        assert "<!--" not in new_text, "metadata header should be stripped"
        assert "proposed_at" not in new_text


def test_apply_proposal_deletes_proposal_file():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "lambda")
        m = _fresh_manager(tmp)
        ok, p = m.propose_patch("lambda", "r", "---\nname: lambda\n---\n\nbody\n")
        assert ok
        assert os.path.isfile(p)
        m.apply_proposal("lambda")
        assert not os.path.isfile(p), "proposal file should be deleted after apply"


def test_apply_proposal_returns_error_when_no_pending():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "mu")
        m = _fresh_manager(tmp)
        ok, msg = m.apply_proposal("mu")
        assert not ok and "no pending" in msg.lower()


# ============================================================
# reject_proposal
# ============================================================

def test_reject_proposal_deletes_all_pending():
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "nu")
        m = _fresh_manager(tmp)
        m.propose_patch("nu", "r1", "body 1")
        _t.sleep(1.05)
        m.propose_patch("nu", "r2", "body 2")
        assert len(m.list_proposals()) == 2
        ok, msg = m.reject_proposal("nu")
        assert ok and "2" in msg, msg
        assert len(m.list_proposals()) == 0


def test_reject_proposal_returns_error_when_no_pending():
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill(tmp, "xi")
        m = _fresh_manager(tmp)
        ok, msg = m.reject_proposal("xi")
        assert not ok


# ============================================================
# tool_skill_propose_patch (the agent-callable wrapper)
# ============================================================

def test_tool_returns_noop_when_flag_off():
    """Critical safety rail: tool MUST refuse work when feature flag is False."""
    old = sa.CONFIG.enable_skill_patching
    try:
        sa.CONFIG.enable_skill_patching = False
        out = sa.tool_skill_propose_patch({
            "name": "any",
            "reason": "x",
            "new_content": "y"
        })
        assert "disabled" in out.lower(), f"expected 'disabled' message, got: {out}"
    finally:
        sa.CONFIG.enable_skill_patching = old


def test_tool_works_end_to_end_when_flag_on():
    """Smoke-test the tool wrapper: enable flag, write skill, call tool, see proposal."""
    old_flag = sa.CONFIG.enable_skill_patching
    old_workspace = sa.CONFIG.workspace
    try:
        with tempfile.TemporaryDirectory() as tmp:
            _write_skill(tmp, "omicron")
            sa.CONFIG.workspace = tmp
            sa.CONFIG.enable_skill_patching = True
            # Reload SKILLS pointing at tmp
            sa.SKILLS = sa.SkillManager(workspace=tmp, skills_dir=tmp)
            sa.SKILLS.discover()
            out = sa.tool_skill_propose_patch({
                "name": "omicron",
                "reason": "test improvement",
                "new_content": "---\nname: omicron\n---\n\nimproved body\n",
            })
            assert "Patch proposed" in out, out
            # Verify it actually landed on disk
            props = sa.SKILLS.list_proposals()
            assert any(p["skill"] == "omicron" for p in props), (
                f"proposal should be on disk after tool call, got props={props}"
            )
    finally:
        sa.CONFIG.enable_skill_patching = old_flag
        sa.CONFIG.workspace = old_workspace
        # Restore the global SKILLS pointing at real workspace
        sa.SKILLS = sa.SkillManager(workspace=old_workspace, skills_dir=sa.CONFIG.skills_dir)
        sa.SKILLS.discover()


# ============================================================
# Audit log
# ============================================================

def test_audit_log_records_propose_apply_reject():
    """Every event should append a JSONL line with action/skill/ts/extra."""
    old_workspace = sa.CONFIG.workspace
    try:
        with tempfile.TemporaryDirectory() as tmp:
            _write_skill(tmp, "pi")
            sa.CONFIG.workspace = tmp
            sa.SKILLS = sa.SkillManager(workspace=tmp, skills_dir=tmp)
            sa.SKILLS.discover()

            sa._log_skill_patch_event("propose", "pi", reason="r1")
            sa._log_skill_patch_event("apply", "pi", ts="20260101_120000", reason="r1")
            sa._log_skill_patch_event("reject", "pi", count=1)

            log_path = os.path.join(tmp, "audit_logs", "skill_patches.jsonl")
            assert os.path.isfile(log_path), "audit log file should exist"
            lines = [json.loads(l) for l in open(log_path, encoding="utf-8") if l.strip()]
            actions = [l["action"] for l in lines]
            assert actions == ["propose", "apply", "reject"], f"got actions: {actions}"
            assert all(l["skill"] == "pi" for l in lines)
    finally:
        sa.CONFIG.workspace = old_workspace
        sa.SKILLS = sa.SkillManager(workspace=old_workspace, skills_dir=sa.CONFIG.skills_dir)
        sa.SKILLS.discover()


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("V4.9.5 self-patching skills with safety rails")
    print("=" * 60)

    print("\n[Config flag]")
    _run("enable_skill_patching defaults False", test_config_flag_defaults_off)

    print("\n[SkillManager.propose_patch]")
    _run("writes to .proposed/<ts>.md", test_propose_patch_writes_to_proposed_dir)
    _run("does NOT modify live SKILL.md", test_propose_patch_does_not_modify_live_skill)
    _run("rejects unknown skill", test_propose_patch_rejects_unknown_skill)
    _run("rejects empty reason", test_propose_patch_rejects_empty_reason)
    _run("rejects empty new_content", test_propose_patch_rejects_empty_content)
    _run("writes metadata header with reason", test_propose_patch_writes_metadata_header)

    print("\n[list_proposals + get_latest_proposal]")
    _run("empty when none pending", test_list_proposals_empty_when_none_pending)
    _run("parses reason from header", test_list_proposals_includes_reason_from_header)
    _run("get_latest returns most recent ts", test_get_latest_proposal_returns_most_recent_ts)

    print("\n[apply_proposal]")
    _run("writes new_content to live", test_apply_proposal_writes_to_live_skill)
    _run("strips metadata header", test_apply_proposal_strips_metadata_header)
    _run("deletes proposal file after apply", test_apply_proposal_deletes_proposal_file)
    _run("returns error when no pending", test_apply_proposal_returns_error_when_no_pending)

    print("\n[reject_proposal]")
    _run("deletes ALL pending for skill", test_reject_proposal_deletes_all_pending)
    _run("returns error when no pending", test_reject_proposal_returns_error_when_no_pending)

    print("\n[tool_skill_propose_patch wrapper]")
    _run("noop when flag is OFF (safety rail)", test_tool_returns_noop_when_flag_off)
    _run("end-to-end when flag is ON", test_tool_works_end_to_end_when_flag_on)

    print("\n[Audit log]")
    _run("records propose / apply / reject as JSONL", test_audit_log_records_propose_apply_reject)

    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"Result: {passed}/{total} passed")
    if passed != total:
        print()
        print("Failures:")
        for name, ok, msg in RESULTS:
            if not ok:
                print(f"  - {name}: {msg}")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
