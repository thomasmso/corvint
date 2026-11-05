"""
Configuration for the `adtech` CLI.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # --- Credentials ---
    # Read when the instance is created, so create it after `.env` is loaded.
    OPENAI_API_KEY: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""), repr=False
    )

    # --- Agent ---
    # Model turns per audit before the SDK raises `MaxTurnsExceeded`
    MAX_TURNS: int = 30

    # --- Project inspection ---
    # Max files supported per input project (excluding Pods/ and build output). Larger projects
    # raise `UnsupportedProjectError` instead of being audited on partial repository info.
    MAX_FILES: int = 20_000

    # --- Reference data ---
    # Fetched by our code at the start of each audit, never by the model.
    # Newest published AppLovinSDK version (CocoaPods trunk).
    SDK_VERSIONS_URL: str = "https://trunk.cocoapods.org/api/v1/pods/AppLovinSDK"
    # AppLovin's SKAdNetwork IDs (https://support.applovin.com/en/max/ios/overview/skadnetwork).
    SKADNETWORK_IDS_URL: str = "https://skadnetwork-ids.applovin.com/v1/skadnetworkids.json"
    HTTP_TIMEOUT_SECONDS: float = 20.0

    # --- Evals ---
    # Relative to the working directory: run `adtech eval` from the repository root.
    EVAL_SUITE: Path = Path("tests/evals/cases.jsonl")
    # Saved reference data, so scores do not change when AppLovin publishes a release.
    EVAL_REFERENCE_DATA: Path = Path("tests/evals/reference_data.json")

    # --- Parallelism ---
    THREAD_POOL_SIZE: int = 8

    # --- Logging ---
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "[adtech] %(asctime)s %(levelname)s %(message)s"
    # Log every model request/response and tool call arguments/results (openai-agents DEBUG logs).
    # Off by default: the data contains customer code.
    LOG_AGENT_DATA: bool = False
