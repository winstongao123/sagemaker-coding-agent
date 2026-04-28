"""V4.10.6: html skill regression test.

Tests:
1. SkillManager.discover() finds the html skill.
2. Frontmatter description starts with "Use when" (CSO format).
3. auto_trigger is False (explicit-activation only).
4. Three reference HTMLs exist in references/ at expected sizes.
5. SKILL.md content references the workflow patterns the user expects
   (screenshot loop + 3 reference templates + house palette + anti-patterns).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def test_html_skill_is_discovered():
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None, "html skill not discovered by SkillManager"


def test_html_skill_description_uses_cso_format():
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None
    desc = html.description.strip().lower()
    assert desc.startswith("use when"), (
        f"html skill description must start with 'Use when' (CSO R-105); got: {html.description[:80]!r}"
    )


def test_html_skill_auto_trigger_default_off():
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None
    assert html.auto_trigger is False, (
        "html skill must NOT auto-trigger; explicit /skill use only"
    )


def test_html_skill_references_present_and_sized():
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None
    refs_dir = os.path.join(html.base_dir, "references")
    assert os.path.isdir(refs_dir), f"references/ dir missing: {refs_dir}"
    # v4.10.6: thresholds set to match the refreshed sagemaker-repo-native templates
    # (HERMES_VS for tabbed, custom minimal for presentation, PS_FLOWCHART_V4 for flowchart).
    # Each must be substantial enough to be a useful reference, not a stub.
    expected = {
        "tabbed_design.html": 30_000,         # > 30 KB (HERMES_VS_CODING_AGENT-style)
        "presentation_slides.html": 5_000,    # > 5 KB (clean minimal template)
        "flowchart_page.html": 30_000,        # > 30 KB (PS_FLOWCHART_V4-style)
    }
    for filename, min_size in expected.items():
        path = os.path.join(refs_dir, filename)
        assert os.path.exists(path), f"reference missing: {filename}"
        size = os.path.getsize(path)
        assert size >= min_size, (
            f"reference {filename} too small ({size} bytes); did the copy fail?"
        )


def test_fourth_canonical_reference_exists():
    """Codex 2026-04-28 #1: SKILL.md cites compact_v4/MAIN/agent/v3_architecture.html
    as the 4th canonical reference (architecture report style). It lives in the
    runtime, not in skills/html/references/, so it must actually exist for the
    agent's read_file call to succeed."""
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None
    # base_dir for the skill is .../skills/html ; the 4th ref is two levels up
    agent_dir = os.path.dirname(os.path.dirname(html.base_dir))  # MAIN/agent
    fourth_ref = os.path.join(agent_dir, "v3_architecture.html")
    assert os.path.exists(fourth_ref), (
        f"4th canonical reference (v3_architecture.html) missing at {fourth_ref}; "
        f"the html skill cites it for 'architecture report' style requests."
    )
    # Should be readable + non-trivial size (full architecture report)
    assert os.path.getsize(fourth_ref) >= 30_000, (
        f"v3_architecture.html too small ({os.path.getsize(fourth_ref)} bytes); "
        f"expected the full architecture report"
    )


def test_html_skill_body_covers_required_workflow():
    """The skill body must cover the workflow rules the user explicitly asked for:
    screenshot iteration loop, 3 reference templates, house palette, anti-patterns."""
    sa.SKILLS.discover()
    html = sa.SKILLS._cache.get("html")
    assert html is not None
    ok, body = sa.SKILLS.read_skill("html")
    assert ok, f"read_skill failed: {body}"
    required_phrases = [
        "screenshot",                # iteration loop must be documented
        "view_image",                # tells agent how to inspect screenshots
        "_shots/",                   # screenshot output convention
        "tabbed_design.html",        # reference 1
        "presentation_slides.html",  # reference 2
        "flowchart_page.html",       # reference 3
        "Mermaid",                   # diagram support
        "Anti-patterns",             # anti-patterns section
        "no emojis",                 # specific user rule (case-insensitive)
        "HTML IS KING",              # user rule
        "file:///",                  # output URL convention
    ]
    for phrase in required_phrases:
        assert phrase.lower() in body.lower(), (
            f"html SKILL.md missing required content: {phrase!r}"
        )


def test_html_skill_body_under_size_cap():
    """The skill body is loaded into context when activated; 12000-char cap
    is enforced by SkillManager.read_skill. Body should be well under that."""
    sa.SKILLS.discover()
    ok, body = sa.SKILLS.read_skill("html")
    assert ok
    # SkillManager truncates at 12000; we want comfortable headroom.
    assert len(body) < 12_000, (
        f"html SKILL.md body is {len(body)} chars; truncation cap is 12000. "
        f"Trim or move content to references/."
    )


if __name__ == "__main__":
    tests = [
        ("html_skill_is_discovered", test_html_skill_is_discovered),
        ("html_skill_description_uses_cso_format", test_html_skill_description_uses_cso_format),
        ("html_skill_auto_trigger_default_off", test_html_skill_auto_trigger_default_off),
        ("html_skill_references_present_and_sized", test_html_skill_references_present_and_sized),
        ("fourth_canonical_reference_exists", test_fourth_canonical_reference_exists),
        ("html_skill_body_covers_required_workflow", test_html_skill_body_covers_required_workflow),
        ("html_skill_body_under_size_cap", test_html_skill_body_under_size_cap),
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
