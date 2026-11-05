from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from adtech_agents.config import Config
from adtech_agents.github_app import GitHubApp, GitHubError, GitHubRepo, parse_github_url

REPO = GitHubRepo("acme", "puzzle")
Handler = Callable[[httpx.Request], httpx.Response]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/acme/puzzle", REPO),
        ("https://github.com/acme/puzzle.git", REPO),
        ("https://github.com/acme/puzzle/", REPO),
        ("github.com/acme/puzzle", REPO),
        ("git@github.com:acme/puzzle.git", REPO),
        ("ssh://git@github.com/acme/puzzle.git", REPO),
        ("https://gitlab.com/acme/puzzle", None),
        ("https://github.com/acme", None),
        ("https://github.com/acme/puzzle/tree/main", None),
        ("https://github.com.evil.com/acme/puzzle", None),
    ],
)
def test_parse_github_url(url: str, expected: GitHubRepo | None) -> None:
    assert parse_github_url(url) == expected


@pytest.fixture
def key(tmp_path: Path) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _app(tmp_path: Path, key: rsa.RSAPrivateKey, handler: Handler) -> GitHubApp:
    pem = tmp_path / "app.pem"
    pem.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    config = Config(GITHUB_APP_ID="123", GITHUB_APP_PRIVATE_KEY_PATH=str(pem))
    return GitHubApp(config, httpx.Client(transport=httpx.MockTransport(handler)))


def test_installation_token_is_scoped_to_the_repository(
    tmp_path: Path, key: rsa.RSAPrivateKey
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        token = request.headers["Authorization"].removeprefix("Bearer ")
        claims = jwt.decode(token, key.public_key(), algorithms=["RS256"])
        assert claims["iss"] == "123"
        if request.url.path == "/repos/acme/puzzle/installation":
            return httpx.Response(200, json={"id": 7})
        assert request.url.path == "/app/installations/7/access_tokens"
        assert json.loads(request.content) == {
            "repositories": ["puzzle"],
            "permissions": {"contents": "write", "pull_requests": "write"},
        }
        return httpx.Response(201, json={"token": "ghs_test"})

    assert _app(tmp_path, key, handler).installation_token(REPO) == "ghs_test"


def test_app_not_installed(tmp_path: Path, key: rsa.RSAPrivateKey) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    with pytest.raises(GitHubError, match=r"not installed on acme/puzzle: .* 404 Not Found"):
        _app(tmp_path, key, handler).installation_token(REPO)


def test_missing_app_settings() -> None:
    with pytest.raises(GitHubError, match="set GITHUB_APP_ID"):
        GitHubApp(Config(GITHUB_APP_ID="", GITHUB_APP_PRIVATE_KEY_PATH="")).installation_token(REPO)


def test_bot_identity(tmp_path: Path, key: rsa.RSAPrivateKey) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/app":
            return httpx.Response(200, json={"slug": "corvint"})
        assert request.url.path == "/users/corvint[bot]"
        assert request.headers["Authorization"] == "Bearer ghs_test"
        return httpx.Response(200, json={"id": 42})

    app = _app(tmp_path, key, handler)
    identity = ("corvint[bot]", "42+corvint[bot]@users.noreply.github.com")
    assert app.bot_identity("ghs_test") == identity


def test_pull_request_errors_include_github_message(tmp_path: Path, key: rsa.RSAPrivateKey) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = {"message": "Validation Failed", "errors": [{"message": "No commits"}]}
        return httpx.Response(422, json=body)

    app = _app(tmp_path, key, handler)
    with pytest.raises(GitHubError, match="422 Validation Failed"):
        app.create_pull_request(REPO, "ghs_test", "corvint/x", "main", "title", "body")
