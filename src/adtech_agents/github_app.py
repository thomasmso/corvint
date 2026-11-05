"""
GitHub access through our GitHub App, used by our code only (never by the model): it signs a
short-lived JWT with the app's private key and exchanges it for an installation token limited to
one repository, with contents and pull request write access.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import jwt

from adtech_agents.config import Config

_NAME = r"[A-Za-z0-9_.-]+"
_GITHUB_URL_RE = re.compile(
    rf"^(?:https://|ssh://git@|git@)?github\.com[/:]({_NAME})/({_NAME}?)(?:\.git)?/?$"
)
_TOKEN_PERMISSIONS = {"contents": "write", "pull_requests": "write"}


class GitHubError(Exception):
    """
    A GitHub API call failed or the app is not set up, so nothing is pushed.
    """


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str

    def __str__(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_github_url(url: str) -> GitHubRepo | None:
    """
    `https://github.com/o/r`, `github.com/o/r`, `git@github.com:o/r.git` and the like, else `None`.
    """
    match = _GITHUB_URL_RE.match(url.strip())
    return GitHubRepo(match.group(1), match.group(2)) if match else None


class GitHubApp:
    def __init__(self, config: Config, client: httpx.Client | None = None) -> None:
        self._config = config
        self._client = client or httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS)

    def installation_token(self, repo: GitHubRepo) -> str:
        """
        A token for `repo` only, valid for an hour.
        """
        app_jwt = self._jwt()
        try:
            installation = self._request("GET", f"/repos/{repo}/installation", app_jwt)
        except GitHubError as exc:
            raise GitHubError(f"the GitHub App is not installed on {repo}: {exc}") from exc
        token = self._request(
            "POST",
            f"/app/installations/{installation['id']}/access_tokens",
            self._jwt(),
            {"repositories": [repo.name], "permissions": _TOKEN_PERMISSIONS},
        )
        return str(token["token"])

    def default_branch(self, repo: GitHubRepo, token: str) -> str:
        return str(self._request("GET", f"/repos/{repo}", token)["default_branch"])

    def create_pull_request(
        self, repo: GitHubRepo, token: str, head: str, base: str, title: str, body: str
    ) -> str:
        """
        Open a pull request from branch `head` into `base`; returns its URL.
        """
        payload = {"title": title, "head": head, "base": base, "body": body}
        return str(self._request("POST", f"/repos/{repo}/pulls", token, payload)["html_url"])

    def bot_identity(self, token: str) -> tuple[str, str]:
        """
        Commit author name and email of the app's bot user, so commits show as the app's.
        `token` is an installation token: the app JWT only works on `/app` endpoints.
        """
        slug = self._request("GET", "/app", self._jwt())["slug"]
        user = self._request("GET", f"/users/{slug}[bot]", token)
        return f"{slug}[bot]", f"{user['id']}+{slug}[bot]@users.noreply.github.com"

    def _jwt(self) -> str:
        if not self._config.GITHUB_APP_ID or not self._config.GITHUB_APP_PRIVATE_KEY_PATH:
            raise GitHubError("set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY_PATH (see README)")
        try:
            key = Path(self._config.GITHUB_APP_PRIVATE_KEY_PATH).expanduser().read_text()
        except OSError as exc:
            raise GitHubError(f"cannot read the GitHub App private key: {exc}") from exc
        now = int(time.time())
        # Backdated for clock drift; GitHub allows at most 10 minutes
        payload = {"iat": now - 60, "exp": now + 540, "iss": self._config.GITHUB_APP_ID}
        return jwt.encode(payload, key, algorithm="RS256")

    def _request(
        self, method: str, path: str, token: str, payload: dict[str, Any] | None = None
    ) -> Any:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{self._config.GITHUB_API_URL}{path}"
        try:
            response = self._client.request(method, url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise GitHubError(f"{method} {path} failed: {exc}") from exc
        if response.is_error:
            raise GitHubError(f"{method} {path}: {response.status_code} {_message(response)}")
        return response.json()


def _message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:200]
    errors = data.get("errors") if isinstance(data, dict) else None
    message = data.get("message", "") if isinstance(data, dict) else ""
    return f"{message} {errors}" if errors else str(message)
