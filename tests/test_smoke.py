"""Smoke test — proves CI is wired up. Replace with real acceptance tests."""


def test_smoke():
    """The simplest possible test. If this fails, your toolchain is broken."""
    assert 1 + 1 == 2


def test_repo_has_agents_md():
    """An agent-native repo must have AGENTS.md at root."""
    from pathlib import Path

    root = Path(__file__).parent.parent
    assert (root / "AGENTS.md").exists(), "AGENTS.md missing at repo root"


def test_repo_has_design_dir():
    """An agent-native repo must have a docs/design/ dir for feature specs."""
    from pathlib import Path

    root = Path(__file__).parent.parent
    assert (root / "docs" / "design").is_dir(), "docs/design/ missing"
