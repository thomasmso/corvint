"""
Fixture data: regenerate the iOS fixtures under `tests/fixtures/`.

`ios_swift_max_clean` and `ios_objc_max_clean` are hand-written (Podfile and sources); this
script writes their `Info.plist` from the saved eval reference data, then derives one fixture per
defect by copying a clean app and applying changes. XcodeGen then writes a real
`PuzzleQuest.xcodeproj` into every fixture.

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

REFERENCE_DATA = Path(__file__).resolve().parent / "evals" / "reference_data.json"
INFO_PLIST = "PuzzleQuest/Info.plist"
# Random string shaped like an AppLovin SDK key, not a real key.
SDK_KEY = "UZeET0n1kyJYiCe32G9DNDD-Jj2-wRFBwZZiQR4gpHO2kkmADDMl7Ch91_vZKPuBoMOceI0RP0XCwGhWM7hnzj"

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

# --- Swift ---

SWIFT_CLEAN = FIXTURES / "ios_swift_max_clean"
SWIFT_AD_MANAGER = "PuzzleQuest/Ads/AdManager.swift"
SWIFT_APP_DELEGATE = "PuzzleQuest/AppDelegate.swift"
SWIFT_GAME_VIEW_CONTROLLER = "PuzzleQuest/GameViewController.swift"
SWIFT_INTERSTITIAL = "PuzzleQuest/Ads/InterstitialAdController.swift"
SWIFT_REWARDED = "PuzzleQuest/Ads/RewardedAdController.swift"

SWIFT_NO_AD_FORMAT_AD_MANAGER = f"""\
import AppLovinSDK
import Foundation

private let sdkKey = "{SDK_KEY}"

final class AdManager {{
    static let shared = AdManager()

    func initializeSdk() {{
        let settings = ALSdk.shared().settings
        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true
        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "https://puzzlequest.example.com/privacy")
        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "https://puzzlequest.example.com/terms")

        let initConfig = ALSdkInitializationConfiguration(sdkKey: sdkKey) {{ builder in
            builder.mediationProvider = ALMediationProviderMAX
        }}

        ALSdk.shared().initialize(with: initConfig) {{ _ in
            // TODO: start loading ads
        }}
    }}
}}
"""

SWIFT_NO_AD_FORMAT_GAME_VIEW_CONTROLLER = """\
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

SWIFT_DEFECTS: dict[str, list[Change]] = {
    "sdk_outdated": [
        Edit("Podfile", "pod 'AppLovinSDK', '~> 13.6'", "pod 'AppLovinSDK', '13.6.4'"),
    ],
    "mediation_provider_missing": [
        Edit(
            SWIFT_AD_MANAGER,
            "            builder.mediationProvider = ALMediationProviderMAX\n",
            "            builder.testDeviceAdvertisingIdentifiers = []\n",
        ),
    ],
    "sdk_key_missing": [
        Edit(
            SWIFT_AD_MANAGER,
            f'private let sdkKey = "{SDK_KEY}"',
            '// TODO: add the SDK key before release\nprivate let sdkKey = ""',
        ),
    ],
    "init_not_at_launch": [
        Edit(SWIFT_APP_DELEGATE, "        AdManager.shared.initializeSdk()\n\n"),
        Edit(
            SWIFT_GAME_VIEW_CONTROLLER,
            "    @objc private func playTapped() {\n",
            "    @objc private func playTapped() {\n        AdManager.shared.initializeSdk()\n",
        ),
    ],
    "skadnetwork_missing": [DeletePlistKey("SKAdNetworkItems")],
    "no_ad_format": [
        DeleteFile(SWIFT_INTERSTITIAL),
        DeleteFile(SWIFT_REWARDED),
        WriteFile(SWIFT_AD_MANAGER, SWIFT_NO_AD_FORMAT_AD_MANAGER),
        WriteFile(SWIFT_GAME_VIEW_CONTROLLER, SWIFT_NO_AD_FORMAT_GAME_VIEW_CONTROLLER),
    ],
    "ad_load_missing": [
        Edit(SWIFT_AD_MANAGER, "            interstitial.load()\n"),
    ],
    "ad_delegate_missing": [
        Edit(SWIFT_REWARDED, "        rewardedAd.delegate = self\n"),
    ],
    "ad_reload_missing": [
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didHide(_ ad: MAAd) {\n        interstitialAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {}",
        ),
    ],
    "network_missing": [
        Edit("Podfile", "  pod 'AppLovinMediationUnityAdsAdapter', '~> 4.20'\n"),
    ],
    "cmp_missing": [
        Edit(
            SWIFT_AD_MANAGER,
            "        let settings = ALSdk.shared().settings\n"
            "        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true\n"
            '        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "https://puzzlequest.example.com/privacy")\n'
            '        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "https://puzzlequest.example.com/terms")\n\n',
        ),
        DeletePlistKey("NSUserTrackingUsageDescription"),
    ],
}

# --- Objective-C ---
# Only defects that live in code: Podfile and Info.plist defects are covered by the Swift set.

OBJC_CLEAN = FIXTURES / "ios_objc_max_clean"
OBJC_AD_MANAGER_H = "PuzzleQuest/Ads/AdManager.h"
OBJC_AD_MANAGER = "PuzzleQuest/Ads/AdManager.m"
OBJC_APP_DELEGATE = "PuzzleQuest/AppDelegate.m"
OBJC_GAME_VIEW_CONTROLLER = "PuzzleQuest/GameViewController.m"
OBJC_INTERSTITIAL = "PuzzleQuest/Ads/InterstitialAdController"
OBJC_REWARDED = "PuzzleQuest/Ads/RewardedAdController"

OBJC_NO_AD_FORMAT_AD_MANAGER_H = """\
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface AdManager : NSObject

+ (instancetype)sharedManager;
- (void)initializeSdk;

@end

NS_ASSUME_NONNULL_END
"""

OBJC_NO_AD_FORMAT_AD_MANAGER = f"""\
#import "AdManager.h"
#import <AppLovinSDK/AppLovinSDK.h>

static NSString *const kSdkKey = @"{SDK_KEY}";

@implementation AdManager

+ (instancetype)sharedManager
{{
    static AdManager *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{{
        shared = [[AdManager alloc] init];
    }});
    return shared;
}}

- (void)initializeSdk
{{
    ALSdkSettings *settings = [ALSdk shared].settings;
    settings.termsAndPrivacyPolicyFlowSettings.enabled = YES;
    settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = [NSURL URLWithString:@"https://puzzlequest.example.com/privacy"];
    settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = [NSURL URLWithString:@"https://puzzlequest.example.com/terms"];

    ALSdkInitializationConfiguration *initConfig = [ALSdkInitializationConfiguration configurationWithSdkKey:kSdkKey builderBlock:^(ALSdkInitializationConfigurationBuilder *builder) {{
        builder.mediationProvider = ALMediationProviderMAX;
    }}];

    [[ALSdk shared] initializeWithConfiguration:initConfig completionHandler:^(ALSdkConfiguration *sdkConfig) {{
        // TODO: start loading ads
    }}];
}}

@end
"""

OBJC_NO_AD_FORMAT_GAME_VIEW_CONTROLLER = """\
#import "GameViewController.h"

@interface GameViewController ()
@property (nonatomic, strong) UIButton *playButton;
@property (nonatomic, assign) NSInteger level;
@end

@implementation GameViewController

- (void)viewDidLoad
{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor systemBackgroundColor];
    self.level = 1;

    self.playButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.playButton setTitle:@"Play" forState:UIControlStateNormal];
    [self.playButton addTarget:self action:@selector(playTapped) forControlEvents:UIControlEventTouchUpInside];
    self.playButton.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.playButton];
    [NSLayoutConstraint activateConstraints:@[
        [self.playButton.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.playButton.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
    ]];
}

- (void)playTapped
{
    // Gameplay is out of scope for this fixture; finishing a level is simulated.
    self.level += 1;
}

@end
"""

OBJC_DEFECTS: dict[str, list[Change]] = {
    "mediation_provider_missing": [
        Edit(
            OBJC_AD_MANAGER,
            "        builder.mediationProvider = ALMediationProviderMAX;\n",
            "        builder.testDeviceAdvertisingIdentifiers = @[];\n",
        ),
    ],
    "sdk_key_missing": [
        Edit(
            OBJC_AD_MANAGER,
            f'static NSString *const kSdkKey = @"{SDK_KEY}";',
            '// TODO: add the SDK key before release\nstatic NSString *const kSdkKey = @"";',
        ),
    ],
    "init_not_at_launch": [
        Edit(OBJC_APP_DELEGATE, "    [[AdManager sharedManager] initializeSdk];\n\n"),
        Edit(
            OBJC_GAME_VIEW_CONTROLLER,
            "- (void)playTapped\n{\n",
            "- (void)playTapped\n{\n    [[AdManager sharedManager] initializeSdk];\n",
        ),
    ],
    "no_ad_format": [
        DeleteFile(f"{OBJC_INTERSTITIAL}.h"),
        DeleteFile(f"{OBJC_INTERSTITIAL}.m"),
        DeleteFile(f"{OBJC_REWARDED}.h"),
        DeleteFile(f"{OBJC_REWARDED}.m"),
        WriteFile(OBJC_AD_MANAGER_H, OBJC_NO_AD_FORMAT_AD_MANAGER_H),
        WriteFile(OBJC_AD_MANAGER, OBJC_NO_AD_FORMAT_AD_MANAGER),
        WriteFile(OBJC_GAME_VIEW_CONTROLLER, OBJC_NO_AD_FORMAT_GAME_VIEW_CONTROLLER),
    ],
    "ad_load_missing": [
        Edit(OBJC_AD_MANAGER, "        [self.interstitial load];\n"),
    ],
    "ad_delegate_missing": [
        Edit(f"{OBJC_REWARDED}.m", "        _rewardedAd.delegate = self;\n"),
    ],
    "ad_reload_missing": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self.interstitialAd loadAd];\n}",
            "- (void)didHideAd:(MAAd *)ad {}",
        ),
    ],
    "cmp_missing": [
        Edit(
            OBJC_AD_MANAGER,
            "    ALSdkSettings *settings = [ALSdk shared].settings;\n"
            "    settings.termsAndPrivacyPolicyFlowSettings.enabled = YES;\n"
            '    settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = [NSURL URLWithString:@"https://puzzlequest.example.com/privacy"];\n'
            '    settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = [NSURL URLWithString:@"https://puzzlequest.example.com/terms"];\n\n',
        ),
        DeletePlistKey("NSUserTrackingUsageDescription"),
    ],
}

APPS: list[tuple[Path, dict[str, list[Change]]]] = [
    (SWIFT_CLEAN, SWIFT_DEFECTS),
    (OBJC_CLEAN, OBJC_DEFECTS),
]


def main() -> None:
    skadnetwork_ids = load_reference_data(REFERENCE_DATA).skadnetwork_ids
    clean_dirs = {clean for clean, _ in APPS}
    for stale in FIXTURES.glob("ios_*_max_*"):
        if stale not in clean_dirs:
            shutil.rmtree(stale)

    for clean, defects in APPS:
        (clean / INFO_PLIST).write_bytes(plistlib.dumps(clean_info_plist(skadnetwork_ids)))
        generate_xcode_project(clean)
        prefix = clean.name.removesuffix("clean")  # e.g. "ios_swift_max_"
        for name, changes in defects.items():
            fixture = FIXTURES / f"{prefix}{name}"
            shutil.copytree(
                clean, fixture, ignore=shutil.ignore_patterns("*.xcodeproj", ".DS_Store")
            )
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
