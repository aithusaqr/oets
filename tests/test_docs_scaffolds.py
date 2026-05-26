"""Tests for the docs/ scaffolds (SCALING.md, ARCHITECTURE.md).

PR A ships these as concept documents. Subsequent PRs will fill in concrete
per-message and per-proto inventories. These tests assert the scaffolds exist
and contain the key concepts they're supposed to explain — without asserting
on schema-specific content that hasn't shipped yet.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCALING_MD = REPO_ROOT / "docs" / "SCALING.md"
ARCHITECTURE_MD = REPO_ROOT / "docs" / "ARCHITECTURE.md"


def test_scaling_md_exists():
    assert SCALING_MD.is_file(), (
        f"docs/SCALING.md not found at {SCALING_MD}; "
        "create it to document the int64 monetary scaling convention"
    )


def test_scaling_md_covers_key_concepts():
    text = SCALING_MD.read_text(encoding="utf-8")
    required = ["price_precision", "size_precision", "int64", "Decimal"]
    missing = [concept for concept in required if concept not in text]
    assert not missing, (
        "docs/SCALING.md is missing these key concepts: "
        + ", ".join(missing)
        + ". The document must explain how int64 fields map back to decimal "
        "values via the precision exponents on InstrumentRef."
    )


def test_architecture_md_exists():
    assert ARCHITECTURE_MD.is_file(), (
        f"docs/ARCHITECTURE.md not found at {ARCHITECTURE_MD}; "
        "create it to document the envelope-bearing vs snapshot/delta split"
    )


def test_architecture_md_covers_three_message_kinds():
    text = ARCHITECTURE_MD.read_text(encoding="utf-8")
    required = ["Event", "snapshot", "delta", "sub-component", "OetsEventEnvelope"]
    missing = [concept for concept in required if concept.lower() not in text.lower()]
    assert not missing, (
        "docs/ARCHITECTURE.md is missing these key concepts: "
        + ", ".join(missing)
        + ". The document must describe the three message kinds (events, "
        "snapshots/deltas, sub-components) and the envelope rule."
    )


def test_readme_links_to_both_docs():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for doc in ("docs/SCALING.md", "docs/ARCHITECTURE.md"):
        assert doc in readme, (
            f"README.md does not link to {doc}; add it to the See Also section "
            "so future contributors discover the convention/design docs."
        )
