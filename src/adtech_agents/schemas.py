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
    allows_latest_version: bool | None = None
    """
    Whether the constraint lets CocoaPods install `RepositoryInfo.latest_sdk_version`. Only
    checked for `AppLovinSDK`; `None` when not checked or the constraint cannot be parsed.
    """


class InfoPlist(BaseModel):
    path: str
    sdk_key_present: bool
    """
    Non-empty `AppLovinSdkKey`.
    """
    tracking_usage_description_present: bool
    """
    Non-empty `NSUserTrackingUsageDescription`.
    """
    skadnetwork_id_count: int
    missing_applovin_skadnetwork_ids: list[str]


class RepositoryInfo(BaseModel):
    platform: Literal["ios", "unknown"]
    dependency_files: list[str]
    """
    `Podfile` paths.
    """
    dependencies: list[Dependency]
    info_plists: list[InfoPlist]
    latest_sdk_version: str
    """
    Newest published `AppLovinSDK` (reference data fetched by our code, not from the repo).
    """


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
