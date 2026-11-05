from __future__ import annotations

import plistlib
import shutil
from pathlib import Path

import pytest

from adtech_agents.config import Config
from adtech_agents.evals import EvalCase, load_cases
from adtech_agents.project_changes import (
    ADMOB_ADAPTER_POD,
    ADMOB_APP_ID_KEY,
    ChangeError,
    apply_changes,
    plan_pod_changes,
)
from adtech_agents.reference_data import ADAPTER_PODS, ReferenceData, load_reference_data
from adtech_agents.tools.inspect_app_project import SDK_POD, allows_version, inspect_app_project
from tests.conftest import REFERENCE_DATA, SUITE, MakeRepo

UNITY_POD = ADAPTER_PODS["UNITY_NETWORK"]
ALL_PODS = [SDK_POD, *ADAPTER_PODS.values()]
REFERENCE = ReferenceData(
    latest_sdk_version="13.7.0",
    adapter_versions={ADMOB_ADAPTER_POD: "13.11.0.0", UNITY_POD: "4.21.0.1"},
    skadnetwork_ids=[],
)
PLACEHOLDER = Config().ADMOB_APP_ID_PLACEHOLDER


def _podfile(*pods: str) -> str:
    return "platform :ios, '15.0'\n\ntarget 'App' do\n" + "".join(pods) + "end\n"


def _plist(**entries: object) -> str:
    return plistlib.dumps({"CFBundleName": "App", **entries}).decode()


def test_adds_missing_adapter_after_applovin_pods(make_repo: MakeRepo) -> None:
    podfile = _podfile(
        "  pod 'AppLovinSDK', '~> 13.6'\n",
        "  pod 'AppLovinMediationGoogleAdapter', '~> 13.9'\n",
        "  pod 'Firebase'\n",
    )
    root = make_repo({"Podfile": podfile})
    [change] = plan_pod_changes(root, [UNITY_POD], REFERENCE, Config())
    assert change.path == "Podfile"
    assert change.new == _podfile(
        "  pod 'AppLovinSDK', '~> 13.6'\n",
        "  pod 'AppLovinMediationGoogleAdapter', '~> 13.9'\n",
        "  pod 'AppLovinMediationUnityAdsAdapter', '4.21.0.1'\n",
        "  pod 'Firebase'\n",
    )
    assert "+  pod 'AppLovinMediationUnityAdsAdapter', '4.21.0.1'\n" in change.diff()


def test_replaces_excluding_constraint_keeping_options_and_comment(make_repo: MakeRepo) -> None:
    root = make_repo(
        {"Podfile": _podfile("  pod 'AppLovinSDK', '13.6.4', :modular_headers => true # pin\n")}
    )
    [change] = plan_pod_changes(root, [SDK_POD], REFERENCE, Config())
    assert change.new == _podfile("  pod 'AppLovinSDK', '13.7.0', :modular_headers => true # pin\n")


def test_leaves_constraints_that_allow_newest_version(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "Podfile": _podfile(
                "  pod 'AppLovinSDK', '~> 13.6'\n",
                "  pod 'AppLovinMediationUnityAdsAdapter', '>= 4.0'\n",
            )
        }
    )
    assert plan_pod_changes(root, [SDK_POD, UNITY_POD], REFERENCE, Config()) == []


def test_admob_adapter_adds_app_id_placeholder_to_app_plist(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "Podfile": _podfile("  pod 'AppLovinSDK', '~> 13.6'\n"),
            "App/Info.plist": _plist(),
            "Widget/Info.plist": _plist(NSExtension={"NSExtensionPointIdentifier": "x"}),
        }
    )
    podfile, plist = plan_pod_changes(root, [ADMOB_ADAPTER_POD], REFERENCE, Config())
    assert podfile.path == "Podfile"
    assert plist.path == "App/Info.plist"
    assert plistlib.loads(plist.new.encode()) == {
        "CFBundleName": "App",
        ADMOB_APP_ID_KEY: PLACEHOLDER,
    }
    added = [line for line in plist.diff().splitlines()[2:] if line.startswith(("+", "-"))]
    assert added == [f"+\t<key>{ADMOB_APP_ID_KEY}</key>", f"+\t<string>{PLACEHOLDER}</string>"]


def test_admob_adapter_keeps_existing_app_id(make_repo: MakeRepo) -> None:
    root = make_repo(
        {
            "Podfile": _podfile("  pod 'AppLovinSDK', '~> 13.6'\n"),
            "App/Info.plist": _plist(GADApplicationIdentifier="ca-app-pub-1~2"),
        }
    )
    [change] = plan_pod_changes(root, [ADMOB_ADAPTER_POD], REFERENCE, Config())
    assert change.path == "Podfile"


@pytest.mark.parametrize(
    ("files", "pods", "message"),
    [
        ({"Podfile": _podfile()}, ["Firebase"], "cannot install Firebase"),
        ({"Podfile": _podfile(), "Other/Podfile": _podfile()}, [SDK_POD], "exactly one Podfile"),
        ({"Podfile": _podfile()}, [UNITY_POD], "must declare once"),
        (
            {"Podfile": _podfile("  pod 'AppLovinSDK'\n", "  pod 'AppLovinSDK', '13.6.4'\n")},
            [SDK_POD],
            "declared 2 times",
        ),
        (
            {"Podfile": _podfile("  pod 'AppLovinSDK', :git => 'x', :branch => '13.6'\n")},
            [SDK_POD],
            None,
        ),
        (
            {"Podfile": _podfile("  pod 'AppLovinSDK', '~> 13.x'\n")},
            [SDK_POD],
            "cannot read the version constraint",
        ),
        (
            {
                "Podfile": _podfile("  pod 'AppLovinSDK', '~> 13.6'\n"),
                "App/Info.plist": _plist(),
                "AppTests/Info.plist": _plist(),
            },
            [ADMOB_ADAPTER_POD],
            "which Info.plist belongs to the app",
        ),
    ],
)
def test_refuses_unsafe_changes(
    make_repo: MakeRepo, files: dict[str, str], pods: list[str], message: str | None
) -> None:
    root = make_repo(files)
    if message is None:  # no version constraint: any version is allowed, nothing to change
        assert plan_pod_changes(root, pods, REFERENCE, Config()) == []
        return
    with pytest.raises(ChangeError, match=message):
        plan_pod_changes(root, pods, REFERENCE, Config())


def test_apply_refuses_files_changed_since_planning(make_repo: MakeRepo) -> None:
    root = make_repo({"Podfile": _podfile("  pod 'AppLovinSDK', '13.6.4'\n")})
    changes = plan_pod_changes(root, [SDK_POD], REFERENCE, Config())
    (root / "Podfile").write_text(_podfile(), encoding="utf-8")
    with pytest.raises(ChangeError, match="changed since"):
        apply_changes(root, changes)
    assert (root / "Podfile").read_text(encoding="utf-8") == _podfile()


# --- Fix evals: install every supported pod in every eval fixture ---

SNAPSHOT = load_reference_data(REFERENCE_DATA)
PODFILE_RULES = {"MAX-SDK-OUTDATED", "MAX-NETWORK-MISSING"}


@pytest.mark.parametrize("case", load_cases(SUITE), ids=lambda case: case.case_id)
def test_installing_pods_fixes_exactly_the_podfile_defects(case: EvalCase, tmp_path: Path) -> None:
    root = tmp_path / "repo"
    shutil.copytree(SUITE.parent / case.fixture, root)
    root = root.resolve()
    changes = plan_pod_changes(root, ALL_PODS, SNAPSHOT, Config())
    assert bool(changes) == any(f.rule_id in PODFILE_RULES for f in case.expected_findings)

    apply_changes(root, changes)
    newest = {SDK_POD: SNAPSHOT.latest_sdk_version, **SNAPSHOT.adapter_versions}
    info = inspect_app_project(root, Config(), SNAPSHOT)
    declared = {d.name: d.version.split(", ") if d.version else [] for d in info.dependencies}
    for pod in ALL_PODS:
        assert allows_version(declared[pod], newest[pod]), pod
    assert plan_pod_changes(root, ALL_PODS, SNAPSHOT, Config()) == []
