"""
install_pods: change the Podfile (and the app's AdMob app ID, if needed) for the requested pods in
an isolated copy of the publisher's repository, build it, and open a pull request (a draft if the
build fails). Shared by every interface.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from adtech_agents.build_check import BuildResult, build_project
from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.github_app import GitHubApp
from adtech_agents.project_changes import (
    ADMOB_APP_ID_KEY,
    FileChange,
    apply_changes,
    plan_pod_changes,
    podfile_path,
)
from adtech_agents.reference_data import ReferenceData, fetch_reference_data
from adtech_agents.workspace import open_pull_request, open_workspace

InstallStep = Literal["copying", "installing_pods", "compiling", "opening_pull_request"]


class InstallResult(BaseModel):
    pull_request_url: str | None
    """
    `None` when every pod already allows its newest version, so there was nothing to change.
    """
    draft: bool = False
    """
    The build failed, so the pull request was opened as a draft.
    """
    build: BuildResult | None = None
    diff: str


def install_pods(
    source: str,
    pods: list[str],
    ctx: Context,
    reference: ReferenceData | None = None,
    github: GitHubApp | None = None,
    on_step: Callable[[InstallStep], None] | None = None,
) -> InstallResult:
    """
    `source` is a local git repository with a GitHub origin, or a GitHub URL. Blocking (git, HTTP
    and the build); never merges or touches the publisher's checkout. `on_step` is called, on
    this thread, as each slow step starts.
    """
    report = on_step or (lambda step: None)
    reference = reference or fetch_reference_data(ctx.config)
    github = github or GitHubApp(ctx.config)
    report("copying")
    workspace = open_workspace(source, github, ctx.config)
    try:
        changes = plan_pod_changes(workspace.root, pods, reference, ctx.config)
        if not changes:
            return InstallResult(pull_request_url=None, diff="")
        apply_changes(workspace.root, changes)
        podfile = workspace.root / podfile_path(workspace.root)
        build = build_project(podfile.parent, ctx.config, report)
        draft = build.status == "failed"
        title = f"Install or update {', '.join(pods)}"
        body = pull_request_body(changes, build, ctx.config)
        paths = [change.path for change in changes]
        report("opening_pull_request")
        url = open_pull_request(workspace, paths, title, body, github, ctx.config, draft=draft)
        return InstallResult(
            pull_request_url=url,
            draft=draft,
            build=build,
            diff="".join(c.diff() for c in changes),
        )
    finally:
        workspace.close()


def pull_request_body(changes: list[FileChange], build: BuildResult, config: Config) -> str:
    lines = [
        "Opened by Corvint, an AppLovin MAX integration assistant. Pod versions are the newest "
        "published ones (CocoaPods trunk for AppLovinSDK, AppLovin's Integration Manager for "
        "adapters).",
        "",
        "Changed files:",
        *(f"- `{change.path}`" for change in changes),
        "",
        *_build_lines(build),
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


def _build_lines(build: BuildResult) -> list[str]:
    match build.status:
        case "succeeded":
            return [
                f"**Build: succeeded.** {build.summary} Not run or tested on a simulator or "
                "device. `Podfile.lock` is not included; run `pod install` to update it.",
            ]
        case "failed":
            return [
                f"**Build: failed, so this is a draft.** {build.summary} From the output:",
                "",
                "```",
                build.log_tail,
                "```",
            ]
        case "skipped":
            return [f"**{build.summary}** Run `pod install` and build the app before merging."]
