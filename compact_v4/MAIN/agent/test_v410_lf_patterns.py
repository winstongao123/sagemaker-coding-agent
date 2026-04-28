"""V4.10.5: Learning_Factory pattern adoption regression tests.

Tests:
1. SYSTEM_PROMPT contains the post-compact resume rule (don't ask user, continue first unchecked task).
2. Compactor.create_summary_prompt includes Standing Constraints (#12) and Critical Don't-Forget Context (#13).
3. Skill self-patch criteria expanded to the 4-rule check (Repeated, Non-trivial, Generalizable, Real-pitfall).
4. Existing doom-loop detection at threshold 3 still in place (we did NOT loosen to LF's 5).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def test_post_compact_resume_rule_in_system_prompt():
    """V4.10.5 LF pattern #2: post-compact protocol must explicitly tell the
    agent to NOT ask the user what to do, and to continue from the first
    unchecked task."""
    sp = sa.SYSTEM_PROMPT
    assert "After auto-compact" in sp, "Post-compact resume rule missing from SYSTEM_PROMPT"
    assert "do NOT ask the user" in sp, "Post-compact rule must explicitly forbid asking user"
    assert "first unchecked task" in sp, "Post-compact rule must tell agent to continue first unchecked task"
    assert "Pending Questions" in sp, "Post-compact rule must reference the Pending Questions section"


def test_summary_prompt_has_standing_constraints_section():
    """V4.10.5 LF pattern #1a: summary prompt must include Standing Constraints
    so hard rules / standing user instructions survive compaction."""
    prompt = sa.Compactor.create_summary_prompt([])
    assert "Standing Constraints" in prompt, "Summary prompt missing Standing Constraints section (#12)"
    # Must explicitly mention what kinds of items qualify
    assert "standing user instructions" in prompt.lower() or "Standing user preferences" in prompt


def test_summary_prompt_has_critical_dont_forget_section():
    """V4.10.5 LF pattern #1b: summary prompt must include Critical Don't-Forget
    Context so the most-important pieces survive compact + are re-orienting."""
    prompt = sa.Compactor.create_summary_prompt([])
    assert "Critical Don't-Forget" in prompt, "Summary prompt missing Critical Don't-Forget Context section (#13)"


def test_skill_promote_criteria_has_4_rule_check():
    """V4.10.5 LF pattern #3: skill self-patching expanded to 4-rule check
    (Repeated + Non-trivial + Generalizable + Real-pitfall)."""
    sp = sa.SYSTEM_PROMPT
    # Look for all 4 explicit rule keywords
    for keyword in ("Repeated", "Non-trivial", "Generalizable", "Real-pitfall"):
        assert keyword in sp, f"Skill promote 4-rule check missing keyword: {keyword!r}"
    # Memory vs skill distinction must be stated
    assert "Memory" in sp and "Skill patches" in sp, (
        "Skill criteria must distinguish memory.md (small facts) from skill patches (procedural knowledge)"
    )


def test_doom_loop_threshold_remains_strict():
    """V4.10.5 sanity: existing 3-repeat doom-loop detector must remain.
    LF uses 5; our 3 is intentionally stricter for self-use. We did NOT loosen."""
    src_path = os.path.join(os.path.dirname(__file__), "sagemaker_agent.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "repeat_count >= 3" in src, "Doom-loop threshold check (>=3) missing"


def test_dynamic_boundary_unchanged_by_lf_additions():
    """V4.10.5 cache safety: the new prompt additions must live BEFORE the
    # === DYNAMIC === boundary (they're system-prompt rules, part of the
    cached prefix). The boundary marker must still be the LAST occurrence
    in SYSTEM_PROMPT — exactly one boundary."""
    sp = sa.SYSTEM_PROMPT
    boundary = "\n\n# === DYNAMIC ==="
    assert sp.count(boundary) == 1, (
        f"SYSTEM_PROMPT must contain exactly 1 cache boundary marker; found {sp.count(boundary)}"
    )
    # Post-compact rule should be in the # System section (above boundary)
    sys_section_end = sp.find(boundary)
    assert sp.find("After auto-compact") < sys_section_end, (
        "Post-compact rule must live in the cached static section, not after boundary"
    )
    # Skill 4-rule check should also be above the boundary (it's part of the # Skill self-patching section)
    assert sp.find("Repeated") < sys_section_end, (
        "Skill 4-rule check must live in the cached static section"
    )


if __name__ == "__main__":
    tests = [
        ("post_compact_resume_rule_in_system_prompt", test_post_compact_resume_rule_in_system_prompt),
        ("summary_prompt_has_standing_constraints_section", test_summary_prompt_has_standing_constraints_section),
        ("summary_prompt_has_critical_dont_forget_section", test_summary_prompt_has_critical_dont_forget_section),
        ("skill_promote_criteria_has_4_rule_check", test_skill_promote_criteria_has_4_rule_check),
        ("doom_loop_threshold_remains_strict", test_doom_loop_threshold_remains_strict),
        ("dynamic_boundary_unchanged_by_lf_additions", test_dynamic_boundary_unchanged_by_lf_additions),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
