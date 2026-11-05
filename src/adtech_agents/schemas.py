"""
Typed data shared by the tools, the agent, the audit and the evals.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from adtech_agents.rules import RuleId, Severity

VerificationStatus = Literal["evidence_verified", "requires_manual_review"]


class Dependency(BaseModel):
    name: str
    version: str | None
    """
    Exactly as written in the file; `None` when the file does not state one.
    """
    source_file: str
    line: int | None


class RepositoryInfo(BaseModel):
    project: str
    platform: Literal["ios", "unknown"]
    dependency_files: list[str]
    """
    `Podfile` paths.
    """
    dependencies: list[Dependency]


# Finding and Evidence double as the agent's structured output, so every field is required
# (nullable where optional) to stay compatible with strict JSON schemas.


class Evidence(BaseModel):
    file_path: str
    line_start: int | None
    line_end: int | None
    description: str


class Finding(BaseModel):
    rule_id: RuleId
    subject: str | None
    title: str
    severity: Severity
    description: str
    evidence: list[Evidence]
    recommendation: str
    verification_status: VerificationStatus


class AgentOutput(BaseModel):
    summary: str
    findings: list[Finding]


class RejectedFinding(BaseModel):
    rule_id: str
    title: str
    reasons: list[str]


class AuditReport(BaseModel):
    summary: str
    findings: list[Finding]
    rejected_findings: list[RejectedFinding]
