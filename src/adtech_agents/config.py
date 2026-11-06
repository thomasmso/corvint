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

    # --- Chat ---
    # Folder under src/adtech_agents/prompts/ with the chat agent's text (only "en" so far).
    CHAT_LOCALE: str = "en"

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
    # Check for newest iOS mediation adapter versions (via AppLovin's Integration Manager API)
    ADAPTER_VERSIONS_URL: str = (
        "https://unity.applovin.com/max/1.0/integration_manager_info?plugin_version=13.6.4"
    )
    HTTP_TIMEOUT_SECONDS: float = 20.0

    # --- Project changes ---
    # Written to the app's Info.plist when installing the AdMob adapter without an AdMob app ID
    # (the Google Mobile Ads SDK crashes at launch without one). The publisher must replace it.
    ADMOB_APP_ID_PLACEHOLDER: str = "ca-app-pub-3555987499888888~8291888888"

    # --- Pull requests (GitHub App, see README) ---
    GITHUB_APP_ID: str = field(default_factory=lambda: os.environ.get("GITHUB_APP_ID", ""))
    # .pem downloaded from the app's settings page; keep it outside the repository.
    GITHUB_APP_PRIVATE_KEY_PATH: str = field(
        default_factory=lambda: os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "")
    )
    GITHUB_API_URL: str = "https://api.github.com"
    # Base URL for clone, fetch and push (tests point it at local bare repositories).
    GITHUB_GIT_URL: str = "https://github.com"
    # Branch pushed for each pull request: prefix + UTC timestamp.
    PULL_REQUEST_BRANCH_PREFIX: str = "corvint/install-pods-"
    GIT_TIMEOUT_SECONDS: float = 300.0

    # --- Evals ---
    # Relative to the working directory: run `adtech eval` from the repository root.
    EVAL_SUITE: Path = Path("tests/evals/cases.jsonl")
    # Saved reference data, so scores do not change when AppLovin publishes a release.
    EVAL_REFERENCE_DATA: Path = Path("tests/evals/reference_data.json")
    # One JSON file per run (git-ignored: reports quote fixture code).
    EVAL_RESULTS_DIR: Path = Path("eval-results")

    # --- Parallelism ---
    THREAD_POOL_SIZE: int = 8

    # --- Logging ---
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "[adtech] %(asctime)s %(levelname)s %(message)s"
    # Log every model request/response and tool call arguments/results (openai-agents DEBUG logs).
    # Off by default: the data contains customer code.
    LOG_AGENT_DATA: bool = False
