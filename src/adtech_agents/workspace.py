"""
An isolated copy of a publisher repository to change, and the pull request that delivers the
change. A local repository gets a git worktree, a GitHub URL is cloned; either way the copy is a
new branch off the GitHub default branch, so the publisher's checkout is never touched.

Git runs with fixed arguments chosen by our code. The installation token goes to git through
environment variables, never on the command line or on disk.
"""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from adtech_agents.config import Config
from adtech_agents.github_app import GitHubApp, GitHubRepo, parse_github_url


class WorkspaceError(Exception):
    """
    The copy could not be created, or the change could not be committed or pushed.
    """


@dataclass
class Workspace:
    root: Path
    """
    The isolated copy; plan and apply changes here.
    """
    repo: GitHubRepo
    base: str
    """
    The GitHub default branch the copy starts from and the pull request targets.
    """
    branch: str
    worktree_of: Path | None
    """
    The publisher's local repository when `root` is a worktree of it, else `None` (a clone).
    """
    temp_dir: Path

    def close(self) -> None:
        """
        Remove the copy (and, for a worktree, its local branch). Pushed branches stay on GitHub.
        """
        if self.worktree_of is not None:
            _git(["worktree", "remove", "--force", str(self.root)], self.worktree_of, check=False)
            _git(["branch", "-D", self.branch], self.worktree_of, check=False)
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def open_workspace(source: str, github: GitHubApp, config: Config) -> Workspace:
    """
    `source` is a local git repository whose `origin` is on GitHub, or a GitHub repository URL.
    """
    local = Path(source).expanduser()
    if local.is_dir():
        local = Path(_git(["rev-parse", "--show-toplevel"], local).strip())
        origin = _git(["remote", "get-url", "origin"], local).strip()
        repo = parse_github_url(origin)
        if repo is None:
            raise WorkspaceError(f"the origin remote of {local} is not a GitHub repository")
    else:
        repo = parse_github_url(source)
        if repo is None:
            raise WorkspaceError(
                f"{source} is neither a local directory nor a GitHub repository URL"
            )

    token = github.installation_token(repo)
    base = github.default_branch(repo, token)
    branch = config.PULL_REQUEST_BRANCH_PREFIX + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    remote = _remote_url(repo, config)
    auth = _auth_env(token, config)
    temp_dir = Path(tempfile.mkdtemp(prefix="corvint-")).resolve()
    root = temp_dir / repo.name
    try:
        if local.is_dir():
            _git(["fetch", "--no-tags", remote, f"refs/heads/{base}"], local, auth)
            _git(["worktree", "add", "--no-track", "-b", branch, str(root), "FETCH_HEAD"], local)
        else:
            _git(["clone", "--depth", "1", "--branch", base, remote, str(root)], temp_dir, auth)
            _git(["switch", "-c", branch], root)
    except WorkspaceError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return Workspace(
        root=root,
        repo=repo,
        base=base,
        branch=branch,
        worktree_of=local if local.is_dir() else None,
        temp_dir=temp_dir,
    )


def open_pull_request(
    workspace: Workspace,
    paths: list[str],
    title: str,
    body: str,
    github: GitHubApp,
    config: Config,
    draft: bool = False,
) -> str:
    """
    Commit the already applied changes to `paths` as the app (and nothing else the build left in
    the copy), push the branch and open a pull request into the default branch; returns its URL.
    The agent never merges.
    """
    if not paths:
        raise WorkspaceError("no changes to submit")
    # Tokens expire after an hour and a chat (or a build) can outlast that, so get a fresh one
    token = github.installation_token(workspace.repo)
    name, email = github.bot_identity(token)
    _git(["add", "--", *paths], workspace.root)
    author = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
    }
    _git(["commit", "-m", title], workspace.root, author)
    remote = _remote_url(workspace.repo, config)
    _git(
        ["push", remote, f"HEAD:refs/heads/{workspace.branch}"],
        workspace.root,
        _auth_env(token, config),
    )
    return github.create_pull_request(
        workspace.repo, token, workspace.branch, workspace.base, title, body, draft
    )


def _remote_url(repo: GitHubRepo, config: Config) -> str:
    return f"{config.GITHUB_GIT_URL}/{repo.owner}/{repo.name}.git"


def _auth_env(token: str, config: Config) -> dict[str, str]:
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"http.{config.GITHUB_GIT_URL}/.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
    }


def _git(args: list[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})},
            capture_output=True,
            text=True,
            timeout=Config.GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkspaceError(f"git {args[0]} failed: {exc}") from exc
    if check and result.returncode != 0:
        raise WorkspaceError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout
