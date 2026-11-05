from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.github_app import GitHubApp, GitHubRepo
from adtech_agents.project_changes import ADMOB_ADAPTER_POD, plan_pod_changes
from adtech_agents.reference_data import ADAPTER_PODS, load_reference_data
from adtech_agents.workflows.install_pods_workflow import install_pods
from adtech_agents.workspace import WorkspaceError, open_pull_request, open_workspace
from tests.conftest import FIXTURES, REFERENCE_DATA

SNAPSHOT = load_reference_data(REFERENCE_DATA)
UNITY_POD = ADAPTER_PODS["UNITY_NETWORK"]
GITHUB_URL = "https://github.com/acme/puzzle"


@dataclass
class PullRequest:
    repo: GitHubRepo
    head: str
    base: str
    title: str
    body: str


@dataclass
class FakeGitHub(GitHubApp):
    pull_requests: list[PullRequest] = field(default_factory=list)

    def installation_token(self, repo: GitHubRepo) -> str:
        return "fake-token"

    def default_branch(self, repo: GitHubRepo, token: str) -> str:
        return "main"

    def create_pull_request(
        self, repo: GitHubRepo, token: str, head: str, base: str, title: str, body: str
    ) -> str:
        self.pull_requests.append(PullRequest(repo, head, base, title, body))
        return f"https://github.com/{repo}/pull/{len(self.pull_requests)}"

    def bot_identity(self, token: str) -> tuple[str, str]:
        return "corvint[bot]", "1+corvint[bot]@users.noreply.github.com"


def git(*args: str, cwd: Path) -> str:
    command = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", *args]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout


@dataclass
class Remote:
    config: Config
    bare: Path
    local: Path
    """
    The publisher's checkout: a clone of `bare` whose origin says github.com.
    """


@pytest.fixture
def remote(tmp_path: Path) -> Remote:
    """
    A fake GitHub: bare repository acme/puzzle seeded with a fixture app on `main`.
    """
    remotes = tmp_path / "remotes"
    bare = remotes / "acme" / "puzzle.git"
    bare.mkdir(parents=True)
    git("init", "--bare", "-b", "main", cwd=bare)
    seed = tmp_path / "seed"
    shutil.copytree(FIXTURES / "ios_swift_max_network_missing", seed)
    git("init", "-b", "main", cwd=seed)
    git("add", ".", cwd=seed)
    git("commit", "-m", "Fixture app (test data)", cwd=seed)
    git("push", str(bare), "main", cwd=seed)

    local = tmp_path / "publisher"
    git("clone", str(bare), str(local), cwd=tmp_path)
    git("remote", "set-url", "origin", f"{GITHUB_URL}.git", cwd=local)
    return Remote(Config(GITHUB_GIT_URL=f"file://{remotes}"), bare, local.resolve())


def test_local_repository_gets_a_worktree_and_stays_untouched(remote: Remote) -> None:
    (remote.local / "Podfile").write_text("work in progress\n", encoding="utf-8")
    github = FakeGitHub()

    workspace = open_workspace(str(remote.local / "PuzzleQuest"), github, remote.config)
    assert workspace.worktree_of == remote.local
    assert "UnityAds" not in (workspace.root / "Podfile").read_text(encoding="utf-8")
    changes = plan_pod_changes(workspace.root, [UNITY_POD], SNAPSHOT, remote.config)
    url = open_pull_request(workspace, changes, "Install Unity", "body", github, remote.config)
    workspace.close()

    assert url == "https://github.com/acme/puzzle/pull/1"
    [pr] = github.pull_requests
    assert (pr.head, pr.base) == (workspace.branch, "main")
    pushed = git("show", f"{workspace.branch}:Podfile", cwd=remote.bare)
    assert "pod 'AppLovinMediationUnityAdsAdapter'" in pushed
    author = git("log", "-1", "--format=%an <%ae>", workspace.branch, cwd=remote.bare)
    assert author.strip() == "corvint[bot] <1+corvint[bot]@users.noreply.github.com>"

    assert (remote.local / "Podfile").read_text(encoding="utf-8") == "work in progress\n"
    assert not workspace.temp_dir.exists()
    assert workspace.branch not in git("branch", "--list", cwd=remote.local)
    assert len(git("worktree", "list", cwd=remote.local).splitlines()) == 1


def test_github_url_is_cloned(remote: Remote) -> None:
    workspace = open_workspace(GITHUB_URL, FakeGitHub(), remote.config)
    assert workspace.worktree_of is None
    assert git("branch", "--show-current", cwd=workspace.root).strip() == workspace.branch
    workspace.close()
    assert not workspace.temp_dir.exists()


def test_install_pods_opens_pull_request_with_admob_placeholder(remote: Remote) -> None:
    github = FakeGitHub()
    ctx = Context.create(remote.config)
    result = install_pods(GITHUB_URL, [ADMOB_ADAPTER_POD, UNITY_POD], ctx, SNAPSHOT, github)
    ctx.shutdown()

    assert result.pull_request_url == "https://github.com/acme/puzzle/pull/1"
    assert "+  pod 'AppLovinMediationUnityAdsAdapter'" in result.diff
    [pr] = github.pull_requests
    assert "**Not built or tested.**" in pr.body
    # The fixture already has an AdMob app ID, so no placeholder warning
    assert "placeholder" not in pr.body


def test_install_pods_with_nothing_to_change_opens_no_pull_request(remote: Remote) -> None:
    github = FakeGitHub()
    ctx = Context.create(remote.config)
    result = install_pods(GITHUB_URL, [ADMOB_ADAPTER_POD], ctx, SNAPSHOT, github)
    ctx.shutdown()
    assert result.pull_request_url is None
    assert github.pull_requests == []


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("https://gitlab.com/acme/puzzle", "neither a local directory nor a GitHub"),
        ("https://github.com/acme/other", "git clone failed"),
    ],
)
def test_bad_sources_fail(remote: Remote, source: str, message: str) -> None:
    with pytest.raises(WorkspaceError, match=message):
        open_workspace(source, FakeGitHub(), remote.config)


def test_local_repository_must_have_github_origin(remote: Remote) -> None:
    git("remote", "set-url", "origin", "https://gitlab.com/acme/puzzle.git", cwd=remote.local)
    with pytest.raises(WorkspaceError, match="not a GitHub repository"):
        open_workspace(str(remote.local), FakeGitHub(), remote.config)


def test_pull_request_needs_changes(remote: Remote) -> None:
    github = FakeGitHub()
    workspace = open_workspace(GITHUB_URL, github, remote.config)
    with pytest.raises(WorkspaceError, match="no changes"):
        open_pull_request(workspace, [], "title", "body", github, remote.config)
    workspace.close()
