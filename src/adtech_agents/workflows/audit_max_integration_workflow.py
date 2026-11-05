"""
`audit_max_integration`: run the agent, then reject findings that cite nonexistent lines.
"""

from __future__ import annotations

from pathlib import Path

from agents import RunConfig, Runner

from adtech_agents.agents.ios_max_audit_agent import build_ios_max_audit_agent
from adtech_agents.context import Context
from adtech_agents.schemas import AgentOutput, AuditReport, Evidence, Finding, RejectedFinding
from adtech_agents.step_logger import StepLogger
from adtech_agents.tools.code_search import read_repo_lines
from adtech_agents.tools.common import AuditContext, ToolError
from adtech_agents.tools.inspect_app_project import inspect_app_project

# TODO: In the future, this workflow-specific task can be used to
# pass run-specific information such as a focus, publisher context, etc.
TASK = "Audit the AppLovin MAX integration of this repository."


async def audit_max_integration(repo_path: Path, ctx: Context) -> AuditReport:
    """
    Audit the AppLovin MAX integration of a repository.
    """
    root = repo_path.resolve()
    result = await Runner.run(
        build_ios_max_audit_agent(),
        TASK,
        context=AuditContext(
            repo_root=root,
            repository_info=inspect_app_project(root, ctx.config),
        ),
        max_turns=ctx.config.MAX_TURNS,
        hooks=StepLogger(),
        run_config=RunConfig(tracing_disabled=True),
    )
    output = result.final_output_as(AgentOutput)
    findings, rejected = validate_findings(output.findings, root)
    return AuditReport(summary=output.summary, findings=findings, rejected_findings=rejected)


def validate_findings(
    findings: list[Finding], root: Path
) -> tuple[list[Finding], list[RejectedFinding]]:
    """
    Check each finding's citations against the repository:

    - no citation checks out: rejected, with the reasons
    - some check out: kept with only those, marked `requires_manual_review`
    - all check out: kept unchanged
    """
    kept: list[Finding] = []
    rejected: list[RejectedFinding] = []

    for finding in findings:
        good_evidence: list[Evidence] = []
        problems: list[str] = []
        for evidence in finding.evidence:
            problem = _find_citation_problem(evidence, root)
            if problem is None:
                good_evidence.append(evidence)
            else:
                problems.append(problem)

        if not good_evidence:
            rejected.append(
                RejectedFinding(
                    rule_id=finding.rule_id,
                    title=finding.title,
                    reasons=problems or ["no evidence cited"],
                )
            )
            continue

        if problems:
            finding = finding.model_copy(
                update={"evidence": good_evidence, "verification_status": "requires_manual_review"}
            )
        kept.append(finding)

    return kept, rejected


def _find_citation_problem(evidence: Evidence, root: Path) -> str | None:
    """
    What is wrong with a citation, or `None` if the file exists and the lines are inside it.
    """
    try:
        _, lines = read_repo_lines(evidence.file_path, root)
    except ToolError as exc:
        return f"{evidence.file_path}: {exc}"

    # No line range: the citation is the whole file (e.g. a Podfile).
    if evidence.line_start is None:
        return None

    start = evidence.line_start
    end = evidence.line_end if evidence.line_end is not None else start
    if not 1 <= start <= end <= len(lines):
        return f"{evidence.file_path}: lines {start}-{end} are outside the file (1-{len(lines)})"
    return None
