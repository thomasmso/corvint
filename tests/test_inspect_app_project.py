from __future__ import annotations

import pytest

from adtech_agents.config import Config
from adtech_agents.tools.inspect_app_project import UnsupportedProjectError, inspect_app_project
from tests.conftest import FIXTURES, MakeRepo


def test_ios_podfile() -> None:
    repository_info = inspect_app_project(FIXTURES / "ios_cocoapods_max", Config())
    assert repository_info.platform == "ios"
    assert repository_info.dependency_files == ["Podfile"]
    versions = {d.name: d.version for d in repository_info.dependencies}
    assert versions["AppLovinSDK"] == "~> 13.6"
    assert versions["AppLovinMediationUnityAdsAdapter"] is None


def test_pods_and_derived_data_are_skipped(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "Podfile": "pod 'AppLovinSDK', '13.6.4'\n",
            "Pods/AppLovinSDK/Podfile": "pod 'AppLovinSDK', '1.0.0'\n",
            "DerivedData/Podfile": "pod 'AppLovinSDK', '1.0.0'\n",
        }
    )
    repository_info = inspect_app_project(root, Config())
    assert repository_info.dependency_files == ["Podfile"]
    assert [d.version for d in repository_info.dependencies] == ["13.6.4"]


def test_unity_project_is_unsupported(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "ProjectSettings/ProjectVersion.txt": "m_EditorVersion: 6000.0.30f1\n",
            "Builds/iOS/Podfile": "pod 'AppLovinSDK', '13.6.4'\n",
            "Builds/iOS/Unity-iPhone.xcodeproj/project.pbxproj": "",
        }
    )
    with pytest.raises(UnsupportedProjectError, match="Unity"):
        inspect_app_project(root, Config())


def test_too_many_files_is_unsupported(make_repo: MakeRepo) -> None:
    root = make_repo({"a.swift": "", "b.swift": "", "c.swift": ""})
    with pytest.raises(UnsupportedProjectError, match="more than 2 files"):
        inspect_app_project(root, Config(MAX_FILES=2))
