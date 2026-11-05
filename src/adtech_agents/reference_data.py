"""
Reference data from outside the repository, fetched by our code from the fixed URLs in `Config`
(never by the model): the newest published AppLovinSDK version and AppLovin's SKAdNetwork IDs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from adtech_agents.config import Config


class ReferenceDataError(Exception):
    """
    Reference data could not be fetched, so the run stops instead of auditing without it.
    """


class ReferenceData(BaseModel):
    latest_sdk_version: str
    """
    Newest `AppLovinSDK` release on CocoaPods trunk (pre-releases excluded).
    """
    skadnetwork_ids: list[str]
    """
    AppLovin's SKAdNetwork IDs, lowercase.
    """


def fetch_reference_data(config: Config) -> ReferenceData:
    versions = _get_json(config.SDK_VERSIONS_URL, config)["versions"]
    releases = [v["name"] for v in versions if all(p.isdigit() for p in v["name"].split("."))]
    if not releases:
        raise ReferenceDataError(f"no AppLovinSDK releases at {config.SDK_VERSIONS_URL}")

    skan = _get_json(config.SKADNETWORK_IDS_URL, config)["skadnetwork_ids"]
    return ReferenceData(
        latest_sdk_version=max(releases, key=version_key),
        skadnetwork_ids=sorted(item["skadnetwork_id"].lower() for item in skan),
    )


def load_reference_data(path: Path) -> ReferenceData:
    return ReferenceData.model_validate_json(path.read_text(encoding="utf-8"))


def version_key(version: str) -> tuple[int, ...]:
    """
    `"13.6.4"` -> `(13, 6, 4)`, for comparing numeric versions.
    """
    return tuple(int(part) for part in version.split("."))


def _get_json(url: str, config: Config) -> Any:
    try:
        response = httpx.get(url, timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ReferenceDataError(f"cannot fetch {url}: {exc}") from exc
