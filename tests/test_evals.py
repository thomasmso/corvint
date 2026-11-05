from __future__ import annotations

import json
from pathlib import Path

from adtech_agents.evals import (
    CaseScore,
    EvalCase,
    ExpectedFinding,
    load_cases,
    save_results,
    score_case,
)
from adtech_agents.schemas import Evidence, Finding
from tests.conftest import SUITE


def _finding(rule_id: str, file_path: str, subject: str | None = None) -> Finding:
    return Finding(
        rule_id=rule_id,  # type: ignore[arg-type]
        subject=subject,
        title="t",
        severity="medium",
        description="d",
        evidence=[Evidence(file_path=file_path, line_start=None, line_end=None, description="e")],
        recommendation="r",
        verification_status="evidence_verified",
    )


def test_suite_loads_and_fixtures_exist() -> None:
    cases = load_cases(SUITE)
    assert len({case.case_id for case in cases}) == len(cases)
    assert all((SUITE.parent / case.fixture).is_dir() for case in cases)


def test_scoring_counts_hits_false_alarms_and_misses() -> None:
    case = EvalCase(
        case_id="c",
        fixture="f",
        description="d",
        expected_findings=[
            ExpectedFinding(rule_id="MAX-OTHER", subject="delegate", files=["a.swift"]),
            ExpectedFinding(rule_id="MAX-INIT-MISSING", files=["b.swift"]),
        ],
        acceptable_findings=[ExpectedFinding(rule_id="MAX-LOAD-BEFORE-INIT", files=["b.swift"])],
    )
    findings = [
        _finding("MAX-OTHER", "a.swift", subject="delegate"),
        _finding("MAX-OTHER", "a.swift", subject="banner"),
        _finding("MAX-LOAD-BEFORE-INIT", "b.swift"),
        _finding("MAX-INIT-MISSING", "elsewhere.swift"),
    ]
    score = score_case(findings, case)
    assert (score.tp, score.fp, score.fn) == (1, 2, 1)
    assert score.false_positives == ["MAX-OTHER (banner): t", "MAX-INIT-MISSING (None): t"]
    assert score.missed == ["MAX-INIT-MISSING (None)"]
    assert not score.passed


def test_results_file_lists_pass_and_fail(tmp_path: Path) -> None:
    passed = CaseScore(case_id="clean", tp=0, fp=0, fn=0)
    failed = CaseScore(case_id="bug", tp=0, fp=0, fn=1, missed=["MAX-INIT-MISSING (None)"])
    results = json.loads(save_results([passed, failed], tmp_path / "results").read_text())
    assert (results["passed"], results["recall"]) == (1, 0.0)
    assert [(c["case_id"], c["passed"], c["missed"]) for c in results["cases"]] == [
        ("clean", True, []),
        ("bug", False, ["MAX-INIT-MISSING (None)"]),
    ]
