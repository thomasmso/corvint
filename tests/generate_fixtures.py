"""
Fixture data: regenerate the iOS fixtures under `tests/fixtures/`.

`ios_max_clean` is hand-written (Podfile and Swift sources); this script writes its `Info.plist`
from the saved eval reference data, then derives one fixture per defect by copying the clean app
and applying changes. XcodeGen then writes a real `PuzzleQuest.xcodeproj` into every fixture.

Run from the repository root (needs `brew install xcodegen`):

    uv run python -m tests.generate_fixtures

Then re-check the line numbers used by the tests.
"""

from __future__ import annotations

import plistlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adtech_agents.reference_data import load_reference_data
from tests.conftest import FIXTURES

CLEAN = FIXTURES / "ios_max_clean"
REFERENCE_DATA = Path(__file__).resolve().parent / "evals" / "reference_data.json"
AD_MANAGER = "PuzzleQuest/Ads/AdManager.swift"
APP_DELEGATE = "PuzzleQuest/AppDelegate.swift"
GAME_VIEW_CONTROLLER = "PuzzleQuest/GameViewController.swift"
INTERSTITIAL = "PuzzleQuest/Ads/InterstitialAdController.swift"
REWARDED = "PuzzleQuest/Ads/RewardedAdController.swift"
INFO_PLIST = "PuzzleQuest/Info.plist"
# Random string shaped like an AppLovin SDK key, not a real key.
SDK_KEY = "UZeET0n1kyJYiCe32G9DNDD-Jj2-wRFBwZZiQR4gpHO2kkmADDMl7Ch91_vZKPuBoMOceI0RP0XCwGhWM7hnzj"
SDK_KEY_LINE = f'private let sdkKey = "{SDK_KEY}"'

PROJECT_YML = """\
name: PuzzleQuest
options:
  bundleIdPrefix: com.puzzlequest
  deploymentTarget:
    iOS: "15.0"
targets:
  PuzzleQuest:
    type: application
    platform: iOS
    sources: [PuzzleQuest]
    settings:
      base:
        INFOPLIST_FILE: PuzzleQuest/Info.plist
        GENERATE_INFOPLIST_FILE: NO
        PRODUCT_BUNDLE_IDENTIFIER: com.puzzlequest.app
        SWIFT_VERSION: "5.0"
"""


def clean_info_plist(skadnetwork_ids: list[str]) -> dict[str, Any]:
    return {
        "CFBundleDevelopmentRegion": "$(DEVELOPMENT_LANGUAGE)",
        "CFBundleDisplayName": "Puzzle Quest",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "$(PRODUCT_BUNDLE_PACKAGE_TYPE)",
        "CFBundleShortVersionString": "1.4.0",
        "CFBundleVersion": "27",
        # Google's published sample AdMob app ID, required by the Google adapter.
        "GADApplicationIdentifier": "ca-app-pub-3940256099942544~1458002511",
        "LSRequiresIPhoneOS": True,
        "NSUserTrackingUsageDescription": (
            "This uses device info for more personalized ads and content."
        ),
        "SKAdNetworkItems": [{"SKAdNetworkIdentifier": i} for i in skadnetwork_ids],
        "UILaunchScreen": {},
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
    }


@dataclass(frozen=True)
class Edit:
    """
    Replace `old` (which must occur exactly once) with `new`.
    """

    file: str
    old: str
    new: str = ""


@dataclass(frozen=True)
class WriteFile:
    file: str
    content: str


@dataclass(frozen=True)
class DeleteFile:
    file: str


@dataclass(frozen=True)
class DeletePlistKey:
    key: str


Change = Edit | WriteFile | DeleteFile | DeletePlistKey

NO_AD_FORMAT_AD_MANAGER = (
    f"""\
import AppLovinSDK
import Foundation

{SDK_KEY_LINE}
"""
    + """
final class AdManager {
    static let shared = AdManager()

    func initializeSdk() {
        let settings = ALSdk.shared().settings
        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true
        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "https://puzzlequest.example.com/privacy")
        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "https://puzzlequest.example.com/terms")

        let initConfig = ALSdkInitializationConfiguration(sdkKey: sdkKey) { builder in
            builder.mediationProvider = ALMediationProviderMAX
        }

        ALSdk.shared().initialize(with: initConfig) { _ in
            // TODO: start loading ads
        }
    }
}
"""
)

NO_AD_FORMAT_GAME_VIEW_CONTROLLER = """\
import UIKit

final class GameViewController: UIViewController {
    private let playButton = UIButton(type: .system)
    private var level = 1

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        playButton.setTitle("Play", for: .normal)
        playButton.addTarget(self, action: #selector(playTapped), for: .touchUpInside)
        playButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(playButton)
        NSLayoutConstraint.activate([
            playButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            playButton.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }

    @objc private func playTapped() {
        // Gameplay is out of scope for this fixture; finishing a level is simulated.
        level += 1
    }
}
"""

DEFECTS: dict[str, list[Change]] = {
    "ios_max_sdk_outdated": [
        Edit("Podfile", "pod 'AppLovinSDK', '~> 13.6'", "pod 'AppLovinSDK', '13.6.4'"),
    ],
    "ios_max_mediation_provider_missing": [
        Edit(
            AD_MANAGER,
            "let initConfig = ALSdkInitializationConfiguration(sdkKey: sdkKey) { builder in\n"
            "            builder.mediationProvider = ALMediationProviderMAX\n"
            "        }",
            "let initConfig = ALSdkInitializationConfiguration(sdkKey: sdkKey) { builder in\n"
            "            builder.testDeviceAdvertisingIdentifiers = []\n"
            "        }",
        ),
    ],
    "ios_max_sdk_key_missing": [
        Edit(
            AD_MANAGER,
            SDK_KEY_LINE,
            '// TODO: add the SDK key before release\nprivate let sdkKey = ""',
        ),
    ],
    "ios_max_init_not_at_launch": [
        Edit(APP_DELEGATE, "        AdManager.shared.initializeSdk()\n\n"),
        Edit(
            GAME_VIEW_CONTROLLER,
            "    @objc private func playTapped() {\n",
            "    @objc private func playTapped() {\n        AdManager.shared.initializeSdk()\n",
        ),
    ],
    "ios_max_skadnetwork_missing": [DeletePlistKey("SKAdNetworkItems")],
    "ios_max_no_ad_format": [
        DeleteFile(INTERSTITIAL),
        DeleteFile(REWARDED),
        WriteFile(AD_MANAGER, NO_AD_FORMAT_AD_MANAGER),
        WriteFile(GAME_VIEW_CONTROLLER, NO_AD_FORMAT_GAME_VIEW_CONTROLLER),
    ],
    "ios_max_ad_load_missing": [
        Edit(AD_MANAGER, "            interstitial.load()\n"),
    ],
    "ios_max_ad_delegate_missing": [
        Edit(REWARDED, "        rewardedAd.delegate = self\n"),
    ],
    "ios_max_ad_reload_missing": [
        Edit(
            INTERSTITIAL,
            "    func didHide(_ ad: MAAd) {\n        interstitialAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {}",
        ),
    ],
    "ios_max_network_missing": [
        Edit("Podfile", "  pod 'AppLovinMediationUnityAdsAdapter', '~> 4.20'\n"),
    ],
    "ios_max_cmp_missing": [
        Edit(
            AD_MANAGER,
            "        let settings = ALSdk.shared().settings\n"
            "        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true\n"
            "        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "
            '"https://puzzlequest.example.com/privacy")\n'
            "        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "
            '"https://puzzlequest.example.com/terms")\n\n',
        ),
        DeletePlistKey("NSUserTrackingUsageDescription"),
    ],
}


def main() -> None:
    skadnetwork_ids = load_reference_data(REFERENCE_DATA).skadnetwork_ids
    (CLEAN / INFO_PLIST).write_bytes(plistlib.dumps(clean_info_plist(skadnetwork_ids)))
    generate_xcode_project(CLEAN)

    for name, changes in DEFECTS.items():
        fixture = FIXTURES / name
        shutil.rmtree(fixture, ignore_errors=True)
        shutil.copytree(CLEAN, fixture, ignore=shutil.ignore_patterns("*.xcodeproj", ".DS_Store"))
        for change in changes:
            apply(fixture, change)
        generate_xcode_project(fixture)
        print(f"wrote {fixture.relative_to(FIXTURES.parent.parent)}")


def apply(fixture: Path, change: Change) -> None:
    match change:
        case Edit(file, old, new):
            path = fixture / file
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise ValueError(f"{fixture.name}/{file}: expected exactly one {old!r}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        case WriteFile(file, content):
            (fixture / file).write_text(content, encoding="utf-8")
        case DeleteFile(file):
            (fixture / file).unlink()
        case DeletePlistKey(key):
            path = fixture / INFO_PLIST
            data = plistlib.loads(path.read_bytes())
            del data[key]
            path.write_bytes(plistlib.dumps(data))


def generate_xcode_project(fixture: Path) -> None:
    spec = fixture / "project.yml"
    spec.write_text(PROJECT_YML, encoding="utf-8")
    try:
        subprocess.run(
            ["xcodegen", "generate", "--quiet", "--spec", str(spec)], check=True, cwd=fixture
        )
    finally:
        spec.unlink()


if __name__ == "__main__":
    main()
