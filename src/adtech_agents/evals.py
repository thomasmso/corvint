"""
Fixture evals: run the audit on each case and count hits, false alarms and misses.

A finding matches an expected one when the rule id matches, the expected subject (if any) appears
in the finding's subject, and at least one evidence file is among the expected files.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from adtech_agents.context import Context
from adtech_agents.reference_data import load_reference_data
from adtech_agents.rules import RuleId
from adtech_agents.schemas import Finding
from adtech_agents.workflows.audit_max_integration_workflow import audit_max_integration


class ExpectedFinding(BaseModel):
    rule_id: RuleId
    subject: str | None = None
    files: list[str]


class EvalCase(BaseModel):
    case_id: str
    fixture: str
    """
    Fixture directory, relative to the suite file.
    """
    description: str
    expected_findings: list[ExpectedFinding] = []
    acceptable_findings: list[ExpectedFinding] = []
    """
    Defensible but not required: neither a hit nor a false alarm.
    """


class CaseScore(BaseModel):
    case_id: str
    tp: int
    fp: int
    fn: int
    error: str | None = None


async def run_suite(ctx: Context) -> list[CaseScore]:
    """
    Run each case; a failed run is recorded as an error so the rest of the suite still runs.
    """
    suite = ctx.config.EVAL_SUITE
    reference_data = load_reference_data(ctx.config.EVAL_REFERENCE_DATA)
    scores = []
    for case in load_cases(suite):
        try:
            report = await audit_max_integration(suite.parent / case.fixture, ctx, reference_data)
        except Exception as exc:
            scores.append(
                CaseScore(
                    case_id=case.case_id, tp=0, fp=0, fn=len(case.expected_findings), error=str(exc)
                )
            )
            continue
        scores.append(score_case(report.findings, case))
    return scores


def load_cases(suite: Path) -> list[EvalCase]:
    lines = suite.read_text(encoding="utf-8").splitlines()
    return [EvalCase.model_validate(json.loads(line)) for line in lines if line.strip()]


def score_case(findings: list[Finding], case: EvalCase) -> CaseScore:
    unmatched = list(findings)
    tp = 0
    for expected in case.expected_findings:
        hit = next((f for f in unmatched if _matches(f, expected)), None)
        if hit:
            unmatched.remove(hit)
            tp += 1
    fp = sum(
        not any(_matches(f, acceptable) for acceptable in case.acceptable_findings)
        for f in unmatched
    )
    return CaseScore(case_id=case.case_id, tp=tp, fp=fp, fn=len(case.expected_findings) - tp)


def render_scores(scores: list[CaseScore]) -> str:
    rows = [f"{'case':36} {'tp':>3} {'fp':>3} {'fn':>3}"]
    rows += [
        f"{s.case_id:36} {s.tp:>3} {s.fp:>3} {s.fn:>3}" + (f"  ERROR: {s.error}" if s.error else "")
        for s in scores
    ]
    tp, fp, fn = (sum(getattr(s, field) for s in scores) for field in ("tp", "fp", "fn"))
    precision = f"{tp / (tp + fp):.2f}" if tp + fp else "n/a"
    recall = f"{tp / (tp + fn):.2f}" if tp + fn else "n/a"
    rows.append(f"\nprecision={precision} recall={recall} false_positives={fp}")
    return "\n".join(rows)


def _matches(finding: Finding, expected: ExpectedFinding) -> bool:
    if finding.rule_id != expected.rule_id:
        return False
    if expected.subject and expected.subject.lower() not in (finding.subject or "").lower():
        return False
    return any(evidence.file_path in expected.files for evidence in finding.evidence)
