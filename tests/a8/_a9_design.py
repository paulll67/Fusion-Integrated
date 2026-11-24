"""Common integrity checks for Assignment 9 frozen specification designs."""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIELDS = {
    "test_id",
    "source_id",
    "purpose",
    "preconditions",
    "action_or_input",
    "expected_result",
    "test_type",
}


def load_cases(strategy: str):
    return json.loads((ROOT / "a9_design" / f"{strategy.upper()}_DESIGN.json").read_text())


def source_corpus(strategy: str) -> str:
    spec_names = {
        "fr": "02_ELM_Functional_Requirement_Specification_v1.5_FINAL.md",
        "uc": "03_ELM_Use_Case_Specifications_v1.4_FINAL.md",
        "br": "04_ELM_Business_Rule_Specifications_v1.4_FINAL.md",
        "wf": "06_ELM_Workflow_Specifications_v1.6_FINAL.md",
    }
    return (ROOT / "docs" / "09-leave" / "specs" / spec_names[strategy]).read_text()


def assert_frozen_design(strategy: str, prefix: str, source_prefixes: tuple[str, ...]):
    cases = load_cases(strategy)
    corpus = source_corpus(strategy)
    assert cases
    for number, case in enumerate(cases, start=1):
        assert set(case) == FIELDS
        assert case["test_id"] == f"A9-{prefix}-{number:03d}"
        assert case["source_id"].startswith(source_prefixes)
        source_key = case["source_id"].split(":", 1)[0].split()[0]
        assert source_key in corpus
        for field in FIELDS - {"test_type"}:
            assert isinstance(case[field], str) and case[field].strip()
        assert case["test_type"] in {
            "authorization",
            "boundary",
            "functional",
            "negative",
            "positive",
            "transition",
            "validation",
        }


@pytest.mark.parametrize(
    ("strategy", "prefix", "source_prefixes"),
    [
        ("fr", "FR", ("AFR-EL-",)),
        ("uc", "UC", ("EL-UC-",)),
        ("br", "BR", ("BR-EL-",)),
        ("wf", "WF", ("BW-EL-", "CW-EL-", "WF-EL-")),
    ],
)
def test_a9_frozen_designs_are_traceable(strategy, prefix, source_prefixes):
    """Every frozen case is schema-valid and traceable to its source specification."""
    assert_frozen_design(strategy, prefix, source_prefixes)
