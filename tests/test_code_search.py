from __future__ import annotations

import pytest

from adtech_agents.tools.code_search import MAX_LINE_CHARS, read_file_lines, search_code
from adtech_agents.tools.common import ToolError
from tests.conftest import FIXTURES, MakeRepo

ROOT = FIXTURES / "ios_swift_max_clean"
AD_MANAGER = "PuzzleQuest/Ads/AdManager.swift"


def test_search_finds_init_with_glob() -> None:
    result = search_code("ALSdk.shared().initialize", "*.swift", False, ROOT)
    assert [(hit.path, hit.line) for hit in result.hits] == [(AD_MANAGER, 24)]
    assert not result.truncated


def test_search_regex_and_invalid_regex() -> None:
    assert search_code(r"ALSdk\.shared\(\)", None, True, ROOT).hits
    with pytest.raises(ToolError, match="invalid regular expression"):
        search_code("(", None, True, ROOT)


def test_literal_alternation_without_hits_says_to_use_regex() -> None:
    with pytest.raises(ToolError, match="set regex to true"):
        search_code("MAInterstitialAd|MARewardedAd", "*.swift", False, ROOT)
    assert len(search_code("MAInterstitialAd|MARewardedAd", "*.swift", True, ROOT).hits) > 1


def test_search_skips_pods_build_and_hidden(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "App/AppDelegate.swift": "ALSdk.shared().initialize(with: config)",
            "Pods/AppLovinSDK/ALSdk.swift": "ALSdk.shared().initialize(with: config)",
            "DerivedData/Build.swift": "ALSdk.shared().initialize(with: config)",
            ".env": "ALSdk.shared().initialize(with: config)",
        }
    )
    assert [hit.path for hit in search_code("initialize", None, False, root).hits] == [
        "App/AppDelegate.swift"
    ]


def test_read_file_lines_numbers_and_caps() -> None:
    excerpt = read_file_lines(AD_MANAGER, 23, 25, ROOT)
    assert excerpt.lines[1].startswith("24: ") and "initialize" in excerpt.lines[1]
    whole = read_file_lines(AD_MANAGER, 1, 10_000, ROOT)
    assert len(whole.lines) == whole.total_lines


def test_long_lines_are_refused_not_cut(make_repo: MakeRepo) -> None:
    long_line = "ALSdk.shared().initialize(with: c) { _ in " + "x" * MAX_LINE_CHARS
    root = make_repo({"App/a.swift": long_line})
    with pytest.raises(ToolError, match=r"App/a\.swift:1 is \d+ chars"):
        search_code("initialize", None, False, root)
    with pytest.raises(ToolError, match=r"App/a\.swift:1 is \d+ chars"):
        read_file_lines("App/a.swift", 1, 1, root)


@pytest.mark.parametrize("path", ["../../etc/passwd", "/etc/passwd", ".env", "App"])
def test_read_refuses_paths_outside_or_hidden(path: str, make_repo: MakeRepo) -> None:
    root = make_repo({".env": "SECRET=1", "App/a.swift": "x"})
    with pytest.raises(ToolError):
        read_file_lines(path, 1, 1, root)


def test_read_refuses_symlink_escape(make_repo: MakeRepo) -> None:
    root = make_repo({"App/a.swift": "x"})
    outside = root.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (root / "link.txt").symlink_to(outside)
    with pytest.raises(ToolError, match="outside the repository"):
        read_file_lines("link.txt", 1, 1, root)
