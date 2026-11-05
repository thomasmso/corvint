from __future__ import annotations

from adtech_agents.schemas import Evidence, Finding
from adtech_agents.workflows.audit_max_integration_workflow import validate_findings
from tests.conftest import FIXTURES

ROOT = FIXTURES / "ios_swift_max_clean"
AD_MANAGER = "PuzzleQuest/Ads/AdManager.swift"


def _finding(title: str, *citations: tuple[str, int | None]) -> Finding:
    return Finding(
        rule_id="MAX-INIT-MISSING",
        subject=None,
        title=title,
        severity="medium",
        description="d",
        evidence=[
            Evidence(file_path=path, line_start=line, line_end=line, description="e")
            for path, line in citations
        ],
        recommendation="r",
        verification_status="evidence_verified",
    )


def test_real_citations_are_kept() -> None:
    kept, rejected = validate_findings(
        [_finding("real", (AD_MANAGER, 24), ("Podfile", None))], ROOT
    )
    assert [(f.title, f.verification_status) for f in kept] == [("real", "evidence_verified")]
    assert rejected == []


def test_partly_bad_citations_need_manual_review() -> None:
    kept, _ = validate_findings([_finding("partial", (AD_MANAGER, 24), (AD_MANAGER, 9999))], ROOT)
    assert kept[0].verification_status == "requires_manual_review"
    assert [e.line_start for e in kept[0].evidence] == [24]


def test_findings_without_real_citations_are_rejected() -> None:
    kept, rejected = validate_findings(
        [
            _finding("missing file", ("PuzzleQuest/DoesNotExist.swift", 1)),
            _finding("escapes repo", ("../../etc/passwd", 1)),
            _finding("no evidence"),
        ],
        ROOT,
    )
    assert kept == []
    assert [r.title for r in rejected] == ["missing file", "escapes repo", "no evidence"]
    assert rejected[2].reasons == ["no evidence cited"]
