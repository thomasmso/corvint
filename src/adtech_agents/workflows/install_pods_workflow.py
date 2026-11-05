"""
install_pods: change the Podfile (and the app's AdMob app ID, if needed) for the requested pods in
an isolated copy of the publisher's repository and open a pull request. Shared by every interface.
"""

from __future__ import annotations

from pydantic import BaseModel

from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.github_app import GitHubApp
from adtech_agents.project_changes import ADMOB_APP_ID_KEY, FileChange, plan_pod_changes
from adtech_agents.reference_data import ReferenceData, fetch_reference_data
from adtech_agents.workspace import open_pull_request, open_workspace


class InstallResult(BaseModel):
    pull_request_url: str | None
    """
    `None` when every pod already allows its newest version, so there was nothing to change.
    """
    diff: str


def install_pods(
    source: str,
    pods: list[str],
    ctx: Context,
    reference: ReferenceData | None = None,
    github: GitHubApp | None = None,
) -> InstallResult:
    """
    `source` is a local git repository with a GitHub origin, or a GitHub URL. Blocking (git and
    HTTP); never builds, merges or touches the publisher's checkout.
    """
    reference = reference or fetch_reference_data(ctx.config)
    github = github or GitHubApp(ctx.config)
    workspace = open_workspace(source, github, ctx.config)
    try:
        changes = plan_pod_changes(workspace.root, pods, reference, ctx.config)
        if not changes:
            return InstallResult(pull_request_url=None, diff="")
        title = f"Install or update {', '.join(pods)}"
        body = pull_request_body(changes, ctx.config)
        url = open_pull_request(workspace, changes, title, body, github, ctx.config)
        return InstallResult(pull_request_url=url, diff="".join(c.diff() for c in changes))
    finally:
        workspace.close()


def pull_request_body(changes: list[FileChange], config: Config) -> str:
    lines = [
        "Opened by Corvint, an AppLovin MAX integration assistant. Pod versions are the newest "
        "published ones (CocoaPods trunk for AppLovinSDK, AppLovin's Integration Manager for "
        "adapters).",
        "",
        "Changed files:",
        *(f"- `{change.path}`" for change in changes),
        "",
        "**Not built or tested.** Run `pod install` and build the app before merging.",
        "",
        "Mediation setup in the MAX dashboard (enabling networks, ad unit IDs) is not part of this "
        "change.",
    ]
    placeholder = [
        c.path for c in changes if ADMOB_APP_ID_KEY in c.new and ADMOB_APP_ID_KEY not in c.old
    ]
    if placeholder:
        lines += [
            "",
            f"**Replace the placeholder AdMob app ID** `{config.ADMOB_APP_ID_PLACEHOLDER}` "
            f"(`{ADMOB_APP_ID_KEY}` in `{placeholder[0]}`) with your app's ID from the AdMob "
            "console. The Google Mobile Ads SDK requires this key; AdMob will not serve ads with "
            "the placeholder.",
        ]
    return "\n".join(lines) + "\n"
