from __future__ import annotations

import pytest

from adtech_agents.config import Config
from adtech_agents.reference_data import ReferenceData, load_reference_data
from adtech_agents.schemas import RepositoryInfo
from adtech_agents.tools.code_search import MAX_LINE_CHARS, iter_files, read_text
from adtech_agents.tools.inspect_app_project import (
    UnsupportedProjectError,
    allows_version,
    inspect_app_project,
)
from tests.conftest import FIXTURES, REFERENCE_DATA, MakeRepo

SNAPSHOT = load_reference_data(REFERENCE_DATA)
REFERENCE = ReferenceData(latest_sdk_version="13.7.0", skadnetwork_ids=["a.sk"])
INFO_PLIST = "PuzzleQuest/Info.plist"


def test_clean_fixture() -> None:
    info = inspect_app_project(FIXTURES / "ios_swift_max_clean", Config(), SNAPSHOT)
    assert info.platform == "ios"
    assert info.dependency_files == ["Podfile"]
    assert {d.name: (d.version, d.allows_latest_version) for d in info.dependencies} == {
        "AppLovinSDK": ("~> 13.6", True),
        "AppLovinMediationGoogleAdapter": ("~> 13.9", None),
        "AppLovinMediationUnityAdsAdapter": ("~> 4.20", None),
    }
    [plist] = info.info_plists
    assert plist.path == INFO_PLIST
    assert not plist.sdk_key_present  # the key is in the init configuration
    assert plist.tracking_usage_description_present
    assert plist.skadnetwork_id_count == len(SNAPSHOT.skadnetwork_ids)
    assert plist.missing_applovin_skadnetwork_ids == []


def test_defect_fixtures() -> None:
    def inspect(fixture: str) -> RepositoryInfo:
        return inspect_app_project(FIXTURES / fixture, Config(), SNAPSHOT)

    outdated = inspect("ios_swift_max_sdk_outdated")
    assert [d.allows_latest_version for d in outdated.dependencies if d.name == "AppLovinSDK"] == [
        False
    ]
    no_skan = inspect("ios_swift_max_skadnetwork_missing")
    assert no_skan.info_plists[0].skadnetwork_id_count == 0
    assert no_skan.info_plists[0].missing_applovin_skadnetwork_ids == SNAPSHOT.skadnetwork_ids
    no_att = inspect("ios_swift_max_cmp_missing")
    assert not no_att.info_plists[0].tracking_usage_description_present


@pytest.mark.parametrize("fixture", sorted(p.name for p in FIXTURES.glob("ios_*_max_*")))
def test_every_fixture_is_an_inspectable_xcode_project(fixture: str) -> None:
    root = FIXTURES / fixture
    assert (root / "PuzzleQuest.xcodeproj" / "project.pbxproj").is_file()
    assert inspect_app_project(root, Config(), SNAPSHOT).info_plists
    for file in iter_files(root):
        text = read_text(root / file) or ""
        assert all(len(line) <= MAX_LINE_CHARS for line in text.splitlines()), file


@pytest.mark.parametrize(
    ("constraints", "expected"),
    [
        ([], True),
        (["13.7.0"], True),
        (["13.6.4"], False),
        (["= 13.6.4"], False),
        (["~> 13.6"], True),
        (["~> 13.6.4"], False),
        (["~> 13"], True),
        (["~> 12.6"], False),
        ([">= 13.6"], True),
        ([">= 13.0", "< 13.7"], False),
        (["!= 13.7.0"], False),
        (["13.7"], True),
        (["latest"], None),
    ],
)
def test_allows_version(constraints: list[str], expected: bool | None) -> None:
    assert allows_version(constraints, "13.7.0") is expected


def test_pods_and_derived_data_are_skipped(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "Podfile": "pod 'AppLovinSDK', '13.6.4'\n",
            "Pods/AppLovinSDK/Podfile": "pod 'AppLovinSDK', '1.0.0'\n",
            "DerivedData/Podfile": "pod 'AppLovinSDK', '1.0.0'\n",
        }
    )
    repository_info = inspect_app_project(root, Config(), REFERENCE)
    assert repository_info.dependency_files == ["Podfile"]
    assert [d.version for d in repository_info.dependencies] == ["13.6.4"]


def test_unreadable_info_plist_is_skipped(make_repo: MakeRepo) -> None:
    root = make_repo({"Podfile": "pod 'AppLovinSDK'\n", "App/Info.plist": "not a plist"})
    assert inspect_app_project(root, Config(), REFERENCE).info_plists == []


def test_unity_project_is_unsupported(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "ProjectSettings/ProjectVersion.txt": "m_EditorVersion: 6000.0.30f1\n",
            "Builds/iOS/Podfile": "pod 'AppLovinSDK', '13.6.4'\n",
            "Builds/iOS/Unity-iPhone.xcodeproj/project.pbxproj": "",
        }
    )
    with pytest.raises(UnsupportedProjectError, match="Unity"):
        inspect_app_project(root, Config(), REFERENCE)


def test_too_many_files_is_unsupported(make_repo: MakeRepo) -> None:
    root = make_repo({"a.swift": "", "b.swift": "", "c.swift": ""})
    with pytest.raises(UnsupportedProjectError, match="more than 2 files"):
        inspect_app_project(root, Config(MAX_FILES=2), REFERENCE)
