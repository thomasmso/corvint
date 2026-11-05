"""
Fixture evals: run the audit on each case and count hits, false alarms and misses.

A finding matches an expected one when the rule id matches, the expected subject (if any) appears
in the finding's subject, and at least one evidence file is among the expected files.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from adtech_agents.context import Context
from adtech_agents.reference_data import load_reference_data
from adtech_agents.rules import RuleId
from adtech_agents.schemas import AuditReport, Finding
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
    false_positives: list[str] = []
    """
    `"<rule_id> (<subject>): <title>"` of each false alarm.
    """
    missed: list[str] = []
    """
    `"<rule_id> (<subject>)"` of each expected finding that was not reported.
    """
    report: AuditReport | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.fp == 0 and self.fn == 0


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
                    case_id=case.case_id,
                    tp=0,
                    fp=0,
                    fn=len(case.expected_findings),
                    error=str(exc),
                    missed=[_describe(expected) for expected in case.expected_findings],
                )
            )
            continue
        score = score_case(report.findings, case)
        scores.append(score.model_copy(update={"report": report}))
    return scores


def save_results(scores: list[CaseScore], results_dir: Path) -> Path:
    """
    Write one JSON file per run: totals, then per case pass/fail, misses, false alarms and the
    full report.
    """
    precision, recall = _precision_recall(scores)
    results = {
        "precision": precision,
        "recall": recall,
        "passed": sum(s.passed for s in scores),
        "cases": [{"passed": s.passed, **s.model_dump()} for s in scores],
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{datetime.now().strftime('%Y-%m-%dT%H%M%S')}.json"
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return path


def load_cases(suite: Path) -> list[EvalCase]:
    lines = suite.read_text(encoding="utf-8").splitlines()
    return [EvalCase.model_validate(json.loads(line)) for line in lines if line.strip()]


def score_case(findings: list[Finding], case: EvalCase) -> CaseScore:
    unmatched = list(findings)
    tp = 0
    missed = []
    for expected in case.expected_findings:
        hit = next((f for f in unmatched if _matches(f, expected)), None)
        if hit:
            unmatched.remove(hit)
            tp += 1
        else:
            missed.append(_describe(expected))
    false_positives = [
        f"{f.rule_id} ({f.subject}): {f.title}"
        for f in unmatched
        if not any(_matches(f, acceptable) for acceptable in case.acceptable_findings)
    ]
    return CaseScore(
        case_id=case.case_id,
        tp=tp,
        fp=len(false_positives),
        fn=len(case.expected_findings) - tp,
        false_positives=false_positives,
        missed=missed,
    )


def render_scores(scores: list[CaseScore]) -> str:
    rows = [f"{'case':36} {'':4} {'tp':>3} {'fp':>3} {'fn':>3}"]
    for s in scores:
        error = f"  ERROR: {s.error}" if s.error else ""
        status = "pass" if s.passed else "FAIL"
        rows.append(f"{s.case_id:36} {status:4} {s.tp:>3} {s.fp:>3} {s.fn:>3}{error}")
        for missed in s.missed:
            rows.append(f"    missed: {missed}")
        for false_positive in s.false_positives:
            rows.append(f"    false positive: {false_positive}")
    precision, recall = _precision_recall(scores)
    rows.append(
        f"\npassed={sum(s.passed for s in scores)}/{len(scores)} "
        f"precision={_fmt(precision)} recall={_fmt(recall)} "
        f"false_positives={sum(s.fp for s in scores)}"
    )
    return "\n".join(rows)


def _precision_recall(scores: list[CaseScore]) -> tuple[float | None, float | None]:
    tp, fp, fn = (sum(getattr(s, field) for s in scores) for field in ("tp", "fp", "fn"))
    precision = round(tp / (tp + fp), 2) if tp + fp else None
    recall = round(tp / (tp + fn), 2) if tp + fn else None
    return precision, recall


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _describe(expected: ExpectedFinding) -> str:
    return f"{expected.rule_id} ({expected.subject})"


def _matches(finding: Finding, expected: ExpectedFinding) -> bool:
    if finding.rule_id != expected.rule_id:
        return False
    if expected.subject and expected.subject.lower() not in (finding.subject or "").lower():
        return False
    return any(evidence.file_path in expected.files for evidence in finding.evidence)
