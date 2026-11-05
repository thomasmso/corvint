from __future__ import annotations

from typing import Any

import pytest

from adtech_agents import reference_data
from adtech_agents.config import Config
from adtech_agents.reference_data import ReferenceDataError, fetch_reference_data

NETWORKS = {
    "MediatedNetworks": [
        {"Name": "ADMOB_NETWORK", "LatestVersions": {"Android": "25.5.0.0", "Ios": "13.11.0.0"}},
        {"Name": "UNITY_NETWORK", "LatestVersions": {"Android": "4.16.0.0", "Ios": "4.21.0.1"}},
        {"Name": "MOLOCO_NETWORK", "LatestVersions": {"Ios": "4.12.0.0"}},
    ]
}
SKAN = {"skadnetwork_ids": [{"skadnetwork_id": "LUDVB6Z3BS.skadnetwork"}]}


def _serve(responses: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reference_data, "_get_json", lambda url, config: responses[url])


def test_fetch_picks_newest_release_adapters_and_lowercases_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config()
    versions = ["13.6.4", "13.10.0", "13.7.0", "14.0.0-beta1"]
    _serve(
        {
            config.SDK_VERSIONS_URL: {"versions": [{"name": v} for v in versions]},
            config.ADAPTER_VERSIONS_URL: NETWORKS,
            config.SKADNETWORK_IDS_URL: SKAN,
        },
        monkeypatch,
    )
    data = fetch_reference_data(config)
    assert data.latest_sdk_version == "13.10.0"
    assert data.adapter_versions == {
        "AppLovinMediationGoogleAdapter": "13.11.0.0",
        "AppLovinMediationUnityAdsAdapter": "4.21.0.1",
    }
    assert data.skadnetwork_ids == ["ludvb6z3bs.skadnetwork"]


def test_fetch_without_releases_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config()
    _serve({config.SDK_VERSIONS_URL: {"versions": [{"name": "14.0.0-beta1"}]}}, monkeypatch)
    with pytest.raises(ReferenceDataError, match="no AppLovinSDK releases"):
        fetch_reference_data(config)


def test_fetch_without_ios_adapter_version_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config()
    networks = {"MediatedNetworks": [{"Name": "ADMOB_NETWORK", "LatestVersions": {"Ios": "1.0"}}]}
    _serve(
        {
            config.SDK_VERSIONS_URL: {"versions": [{"name": "13.7.0"}]},
            config.ADAPTER_VERSIONS_URL: networks,
        },
        monkeypatch,
    )
    with pytest.raises(ReferenceDataError, match="no iOS adapter version for UNITY_NETWORK"):
        fetch_reference_data(config)
