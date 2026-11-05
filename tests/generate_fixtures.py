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
import re
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
    "ad_reload_missing_on_hide": [
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didHide(_ ad: MAAd) {\n        interstitialAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {}",
        ),
    ],
    "ad_reload_missing_on_display_fail": [
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didFail(toDisplay ad: MAAd, withError error: MAError) {\n"
            "        interstitialAd.load()\n"
            "    }",
            "    func didFail(toDisplay ad: MAAd, withError error: MAError) {}",
        ),
    ],
    "ad_reload_missing_on_load_fail": [
        Edit(
            SWIFT_INTERSTITIAL,
            "        // Retry with exponentially higher delays, up to 64 seconds\n"
            "        retryAttempt += 1\n"
            "        let delaySec = pow(2.0, min(6.0, retryAttempt))\n"
            "        DispatchQueue.main.asyncAfter(deadline: .now() + delaySec) { [weak self] in\n"
            "            self?.interstitialAd.load()\n"
            "        }\n",
            '        print("Interstitial failed to load: \\(error.message)")\n',
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
    "ad_reload_missing_on_hide": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self.interstitialAd loadAd];\n}",
            "- (void)didHideAd:(MAAd *)ad {}",
        ),
    ],
    "ad_reload_missing_on_display_fail": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error\n"
            "{\n"
            "    [self.interstitialAd loadAd];\n"
            "}",
            "- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error {}",
        ),
    ],
    "ad_reload_missing_on_load_fail": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "    // Retry with exponentially higher delays, up to 64 seconds\n"
            "    self.retryAttempt++;\n"
            "    NSInteger delaySec = pow(2, MIN(6, self.retryAttempt));\n"
            "    __weak typeof(self) weakSelf = self;\n"
            "    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, delaySec * NSEC_PER_SEC), "
            "dispatch_get_main_queue(), ^{\n"
            "        [weakSelf.interstitialAd loadAd];\n"
            "    });\n",
            '    NSLog(@"Interstitial failed to load: %@", error.message);\n',
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

# --- Harder cases ---
# clean_*: correct code written in a less obvious way (precision traps).
# decoy_*: one defect next to code that looks like it fixes it but never runs.
# multi_*: several single defects from above combined; their edits must not overlap.
# large_*: the clean app plus unrelated game code, so the agent has to search.


def combine(defects: dict[str, list[Change]], *names: str) -> list[Change]:
    return [change for name in names for change in defects[name]]


UMP_POD = "  pod 'GoogleUserMessagingPlatform', '~> 3.1'\n"
ADD_UMP_POD = Edit(
    "Podfile",
    "  pod 'AppLovinMediationUnityAdsAdapter', '~> 4.20'\n",
    "  pod 'AppLovinMediationUnityAdsAdapter', '~> 4.20'\n" + UMP_POD,
)

# (class name, Int property, doc) of the filler stores in the large_* fixtures.
GAME_STORES = (
    ("Coins", "balance", "Soft currency earned in levels and the shop."),
    ("Hints", "remaining", "Hints the player can spend on a puzzle."),
    ("Lives", "count", "Lives left before the player must wait or refill."),
    ("Stars", "total", "Stars earned across all levels."),
    ("Level", "current", "Highest level the player has unlocked."),
    ("Streak", "days", "Consecutive days the player has opened the game."),
    ("DailyReward", "lastClaimDay", "Day number of the last claimed daily reward."),
    ("Tutorial", "step", "Furthest tutorial step the player has seen."),
    ("Sound", "volume", "Sound effects volume, 0 to 100."),
    ("Music", "volume", "Music volume, 0 to 100."),
    ("Haptics", "intensity", "Haptic feedback intensity, 0 to 3."),
    ("Theme", "selectedIndex", "Index of the selected board theme."),
    ("Achievements", "unlockedCount", "Number of achievements unlocked."),
    ("Leaderboard", "bestScore", "Best score submitted to the leaderboard."),
    ("Inventory", "itemCount", "Number of items in the player's inventory."),
    ("Boosters", "owned", "Boosters the player owns."),
    ("Events", "activeCount", "Live events the player has joined."),
    ("Gifts", "pending", "Gifts from friends waiting to be opened."),
    ("Friends", "count", "Friends connected to the player's profile."),
    ("Badges", "count", "App icon badge count for unread notifications."),
    ("Puzzles", "solved", "Puzzles solved across all modes."),
    ("Chests", "unopened", "Reward chests not opened yet."),
    ("Quests", "completed", "Quests completed this season."),
    ("Skins", "unlocked", "Tile skins unlocked."),
    ("SeasonPass", "tier", "Current season pass tier."),
    ("Tiles", "cleared", "Tiles cleared in total."),
    ("Combo", "best", "Longest combo the player has made."),
    ("Timer", "bestSeconds", "Fastest level completion, in seconds."),
    ("RatingPrompt", "timesShown", "Times the app rating prompt has been shown."),
    ("Sessions", "count", "Number of app sessions."),
)


def defaults_key(name: str) -> str:
    return "puzzlequest." + re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# --- Harder cases: Swift ---

SWIFT_NO_PRIVACY_FLOW = (
    "        let settings = ALSdk.shared().settings\n"
    "        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true\n"
    '        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "https://puzzlequest.example.com/privacy")\n'
    '        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "https://puzzlequest.example.com/terms")\n\n'
)

SWIFT_UMP_INIT = """\
    /// Gathers consent with Google's UMP form and the ATT prompt, then starts MAX.
    func initializeSdk() {
        ConsentInformation.shared.requestConsentInfoUpdate(with: RequestParameters()) { _ in
            ConsentForm.loadAndPresentIfRequired(from: nil) { _ in
                ATTrackingManager.requestTrackingAuthorization { _ in
                    DispatchQueue.main.async {
                        self.startMax()
                    }
                }
            }
        }
    }

    private func startMax() {
"""

SWIFT_APP = """\
import SwiftUI

@main
struct PuzzleQuestApp: App {
    init() {
        AdManager.shared.initializeSdk()
    }

    var body: some Scene {
        WindowGroup {
            GameView()
                .ignoresSafeArea()
        }
    }
}

/// Hosts the UIKit game screen in SwiftUI.
struct GameView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> GameViewController {
        GameViewController()
    }

    func updateUIViewController(_ uiViewController: GameViewController, context: Context) {}
}
"""

SWIFT_QUICK_START_SAMPLE = """\
// AppLovin MAX quick start sample.
import AppLovinSDK
import UIKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        let initConfig = ALSdkInitializationConfiguration(sdkKey: "«SDK-key»") { builder in
            builder.mediationProvider = ALMediationProviderMAX
        }
        ALSdk.shared().initialize(with: initConfig) { sdkConfig in
            // Start loading ads
        }
        return true
    }
}
"""

PROJECT_YML_WITH_EXTENSION = """\
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
    dependencies:
      - target: PuzzleQuestNotifications
    settings:
      base:
        INFOPLIST_FILE: PuzzleQuest/Info.plist
        GENERATE_INFOPLIST_FILE: NO
        PRODUCT_BUNDLE_IDENTIFIER: com.puzzlequest.app
        SWIFT_VERSION: "5.0"
  PuzzleQuestNotifications:
    type: app-extension
    platform: iOS
    sources: [PuzzleQuestNotifications]
    settings:
      base:
        INFOPLIST_FILE: PuzzleQuestNotifications/Info.plist
        GENERATE_INFOPLIST_FILE: NO
        PRODUCT_BUNDLE_IDENTIFIER: com.puzzlequest.app.notifications
        SWIFT_VERSION: "5.0"
"""

NOTIFICATION_SERVICE = """\
import UserNotifications

final class NotificationService: UNNotificationServiceExtension {
    private var contentHandler: ((UNNotificationContent) -> Void)?
    private var bestAttemptContent: UNMutableNotificationContent?

    override func didReceive(
        _ request: UNNotificationRequest,
        withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void
    ) {
        self.contentHandler = contentHandler
        bestAttemptContent = request.content.mutableCopy() as? UNMutableNotificationContent
        if let content = bestAttemptContent {
            content.threadIdentifier = "puzzlequest.daily"
            contentHandler(content)
        }
    }

    override func serviceExtensionTimeWillExpire() {
        if let contentHandler, let content = bestAttemptContent {
            contentHandler(content)
        }
    }
}
"""

NOTIFICATION_EXTENSION_PLIST: dict[str, Any] = {
    "CFBundleDevelopmentRegion": "$(DEVELOPMENT_LANGUAGE)",
    "CFBundleDisplayName": "Puzzle Quest Notifications",
    "CFBundleExecutable": "$(EXECUTABLE_NAME)",
    "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
    "CFBundleInfoDictionaryVersion": "6.0",
    "CFBundleName": "$(PRODUCT_NAME)",
    "CFBundlePackageType": "$(PRODUCT_BUNDLE_PACKAGE_TYPE)",
    "CFBundleShortVersionString": "1.4.0",
    "CFBundleVersion": "27",
    "NSExtension": {
        "NSExtensionPointIdentifier": "com.apple.usernotifications.service",
        "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).NotificationService",
    },
}

SWIFT_SHOP = """\
import UIKit

final class ShopViewController: UIViewController {
    private let watchAdButton = UIButton(type: .system)

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        watchAdButton.setTitle("Watch an ad for 50 coins", for: .normal)
        watchAdButton.addTarget(self, action: #selector(watchAdTapped), for: .touchUpInside)
        watchAdButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(watchAdButton)
        NSLayoutConstraint.activate([
            watchAdButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            watchAdButton.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }

    @objc private func watchAdTapped() {
        AdManager.shared.rewarded?.showIfReady { _ in
            CoinsStore.shared.balance += 50
        }
    }
}
"""


def swift_game_code() -> list[Change]:
    changes: list[Change] = [WriteFile("PuzzleQuest/Shop/ShopViewController.swift", SWIFT_SHOP)]
    for name, prop, doc in GAME_STORES:
        content = f"""\
import Foundation

/// {doc}
final class {name}Store {{
    static let shared = {name}Store()

    private let defaults = UserDefaults.standard
    private let key = "{defaults_key(name)}"

    var {prop}: Int {{
        get {{ defaults.integer(forKey: key) }}
        set {{ defaults.set(newValue, forKey: key) }}
    }}

    func reset() {{
        defaults.removeObject(forKey: key)
    }}
}}
"""
        changes.append(WriteFile(f"PuzzleQuest/Game/{name}Store.swift", content))
    return changes


SWIFT_DEFECTS |= {
    "clean_reload_helper": [
        Edit(
            SWIFT_INTERSTITIAL,
            "        let delaySec = pow(2.0, min(6.0, retryAttempt))\n"
            "        DispatchQueue.main.asyncAfter(deadline: .now() + delaySec) { [weak self] in\n"
            "            self?.interstitialAd.load()\n"
            "        }\n",
            "        loadNextAd(after: pow(2.0, min(6.0, retryAttempt)))\n",
        ),
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didHide(_ ad: MAAd) {\n        interstitialAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {\n        loadNextAd()\n    }",
        ),
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didFail(toDisplay ad: MAAd, withError error: MAError) {\n"
            "        interstitialAd.load()\n",
            "    func didFail(toDisplay ad: MAAd, withError error: MAError) {\n        loadNextAd()\n",
        ),
        Edit(
            SWIFT_INTERSTITIAL,
            "    // MARK: MAAdDelegate\n",
            "    private func loadNextAd(after delaySec: Double = 0) {\n"
            "        DispatchQueue.main.asyncAfter(deadline: .now() + delaySec) { [weak self] in\n"
            "            self?.interstitialAd.load()\n"
            "        }\n"
            "    }\n\n"
            "    // MARK: MAAdDelegate\n",
        ),
    ],
    "clean_lazy_ad_setup": [
        Edit(
            SWIFT_INTERSTITIAL,
            "    private let interstitialAd: MAInterstitialAd\n",
            "    private let adUnitIdentifier: String\n"
            "    private lazy var interstitialAd: MAInterstitialAd = {\n"
            "        let ad = MAInterstitialAd(adUnitIdentifier: adUnitIdentifier)\n"
            "        ad.delegate = self\n"
            "        return ad\n"
            "    }()\n",
        ),
        Edit(
            SWIFT_INTERSTITIAL,
            "        interstitialAd = MAInterstitialAd(adUnitIdentifier: adUnitIdentifier)\n"
            "        super.init()\n"
            "        interstitialAd.delegate = self\n",
            "        self.adUnitIdentifier = adUnitIdentifier\n        super.init()\n",
        ),
    ],
    "clean_ump_consent": [
        ADD_UMP_POD,
        Edit(
            SWIFT_AD_MANAGER,
            "import AppLovinSDK\nimport Foundation\n",
            "import AppLovinSDK\nimport AppTrackingTransparency\nimport Foundation\n"
            "import UserMessagingPlatform\n",
        ),
        Edit(
            SWIFT_AD_MANAGER, "    func initializeSdk() {\n" + SWIFT_NO_PRIVACY_FLOW, SWIFT_UMP_INIT
        ),
    ],
    "clean_swiftui_app": [
        DeleteFile(SWIFT_APP_DELEGATE),
        WriteFile("PuzzleQuest/PuzzleQuestApp.swift", SWIFT_APP),
    ],
    "decoy_commented_load": [
        Edit(
            SWIFT_AD_MANAGER,
            "            interstitial.load()\n",
            "            // interstitial.load()\n",
        ),
    ],
    "decoy_dead_reload": [
        Edit(
            SWIFT_INTERSTITIAL,
            "    func didHide(_ ad: MAAd) {\n        interstitialAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {}\n\n"
            "    private func reloadAfterHide() {\n        interstitialAd.load()\n    }",
        ),
    ],
    "decoy_sample_code": [
        *SWIFT_DEFECTS["mediation_provider_missing"],
        WriteFile("Samples/MAXQuickStart/AppDelegate.swift", SWIFT_QUICK_START_SAMPLE),
    ],
    "decoy_extension_plist": [
        WriteFile("project.yml", PROJECT_YML_WITH_EXTENSION),
        WriteFile("PuzzleQuestNotifications/NotificationService.swift", NOTIFICATION_SERVICE),
        WriteFile(
            "PuzzleQuestNotifications/Info.plist",
            plistlib.dumps(NOTIFICATION_EXTENSION_PLIST).decode(),
        ),
    ],
    "multi_podfile_and_privacy": combine(
        SWIFT_DEFECTS, "sdk_outdated", "network_missing", "cmp_missing"
    ),
    "multi_init_config": combine(
        SWIFT_DEFECTS, "sdk_key_missing", "mediation_provider_missing", "skadnetwork_missing"
    ),
    "multi_ad_lifecycle": combine(
        SWIFT_DEFECTS, "ad_delegate_missing", "ad_reload_missing_on_display_fail"
    ),
    "large_clean": swift_game_code(),
    "large_rewarded_reload_missing_on_hide": [
        *swift_game_code(),
        Edit(
            SWIFT_REWARDED,
            "    func didHide(_ ad: MAAd) {\n        rewardedAd.load()\n    }",
            "    func didHide(_ ad: MAAd) {}",
        ),
    ],
}

# --- Harder cases: Objective-C ---

OBJC_NO_PRIVACY_FLOW = (
    "    ALSdkSettings *settings = [ALSdk shared].settings;\n"
    "    settings.termsAndPrivacyPolicyFlowSettings.enabled = YES;\n"
    '    settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = [NSURL URLWithString:@"https://puzzlequest.example.com/privacy"];\n'
    '    settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = [NSURL URLWithString:@"https://puzzlequest.example.com/terms"];\n\n'
)

OBJC_UMP_INIT = """\
- (void)initializeSdk
{
    // Gather consent with Google's UMP form and the ATT prompt, then start MAX.
    [UMPConsentInformation.sharedInstance requestConsentInfoUpdateWithParameters:[[UMPRequestParameters alloc] init] completionHandler:^(NSError *updateError) {
        [UMPConsentForm loadAndPresentIfRequiredFromViewController:nil completionHandler:^(NSError *formError) {
            [ATTrackingManager requestTrackingAuthorizationWithCompletionHandler:^(ATTrackingManagerAuthorizationStatus status) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self startMax];
                });
            }];
        }];
    }];
}

- (void)startMax
{
"""

OBJC_BOOTSTRAP_H = """\
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Starts the app's services at launch.
@interface AppBootstrap : NSObject

+ (void)startWithLaunchOptions:(nullable NSDictionary *)launchOptions;

@end

NS_ASSUME_NONNULL_END
"""

OBJC_BOOTSTRAP = """\
#import "AppBootstrap.h"
#import "AdManager.h"

@implementation AppBootstrap

+ (void)startWithLaunchOptions:(NSDictionary *)launchOptions
{
    [self registerDefaults];
    [[AdManager sharedManager] initializeSdk];
}

+ (void)registerDefaults
{
    [[NSUserDefaults standardUserDefaults] registerDefaults:@{
        @"puzzlequest.soundEnabled": @YES,
        @"puzzlequest.hapticsEnabled": @YES,
    }];
}

@end
"""

OBJC_QUICK_START_SAMPLE = """\
// AppLovin MAX quick start sample.
#import "AppDelegate.h"
#import <AppLovinSDK/AppLovinSDK.h>

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
    ALSdkInitializationConfiguration *initConfig = [ALSdkInitializationConfiguration configurationWithSdkKey:@"«SDK-key»" builderBlock:^(ALSdkInitializationConfigurationBuilder *builder) {
        builder.mediationProvider = ALMediationProviderMAX;
    }];
    [[ALSdk shared] initializeWithConfiguration:initConfig completionHandler:^(ALSdkConfiguration *sdkConfig) {
        // Start loading ads
    }];
    return YES;
}

@end
"""

OBJC_SHOP_H = """\
#import <UIKit/UIKit.h>

@interface ShopViewController : UIViewController
@end
"""

OBJC_SHOP = """\
#import "ShopViewController.h"
#import "AdManager.h"
#import "PQCoinsStore.h"
#import "RewardedAdController.h"

@interface ShopViewController ()
@property (nonatomic, strong) UIButton *watchAdButton;
@end

@implementation ShopViewController

- (void)viewDidLoad
{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor systemBackgroundColor];

    self.watchAdButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.watchAdButton setTitle:@"Watch an ad for 50 coins" forState:UIControlStateNormal];
    [self.watchAdButton addTarget:self action:@selector(watchAdTapped) forControlEvents:UIControlEventTouchUpInside];
    self.watchAdButton.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.watchAdButton];
    [NSLayoutConstraint activateConstraints:@[
        [self.watchAdButton.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.watchAdButton.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
    ]];
}

- (void)watchAdTapped
{
    [[AdManager sharedManager].rewarded showIfReadyWithReward:^(MAReward *reward) {
        [PQCoinsStore sharedStore].balance += 50;
    }];
}

@end
"""


def objc_game_code() -> list[Change]:
    changes: list[Change] = [
        WriteFile("PuzzleQuest/Shop/ShopViewController.h", OBJC_SHOP_H),
        WriteFile("PuzzleQuest/Shop/ShopViewController.m", OBJC_SHOP),
    ]
    for name, prop, doc in GAME_STORES:
        cls = f"PQ{name}Store"
        header = f"""\
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// {doc}
@interface {cls} : NSObject

@property (nonatomic, assign) NSInteger {prop};

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
"""
        implementation = f"""\
#import "{cls}.h"

static NSString *const kKey = @"{defaults_key(name)}";

@implementation {cls}

+ (instancetype)sharedStore
{{
    static {cls} *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{{
        shared = [[{cls} alloc] init];
    }});
    return shared;
}}

- (NSInteger){prop}
{{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}}

- (void)set{prop[0].upper()}{prop[1:]}:(NSInteger)value
{{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}}

- (void)reset
{{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}}

@end
"""
        changes.append(WriteFile(f"PuzzleQuest/Game/{cls}.h", header))
        changes.append(WriteFile(f"PuzzleQuest/Game/{cls}.m", implementation))
    return changes


OBJC_DEFECTS |= {
    "clean_reload_helper": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "    NSInteger delaySec = pow(2, MIN(6, self.retryAttempt));\n"
            "    __weak typeof(self) weakSelf = self;\n"
            "    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, delaySec * NSEC_PER_SEC), "
            "dispatch_get_main_queue(), ^{\n"
            "        [weakSelf.interstitialAd loadAd];\n"
            "    });\n",
            "    [self loadNextAdAfter:pow(2, MIN(6, self.retryAttempt))];\n",
        ),
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self.interstitialAd loadAd];\n}",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self loadNextAdAfter:0];\n}",
        ),
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error\n"
            "{\n    [self.interstitialAd loadAd];\n}",
            "- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error\n"
            "{\n    [self loadNextAdAfter:0];\n}",
        ),
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "#pragma mark - MAAdDelegate\n",
            "- (void)loadNextAdAfter:(NSTimeInterval)delaySec\n"
            "{\n"
            "    __weak typeof(self) weakSelf = self;\n"
            "    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(delaySec * NSEC_PER_SEC)), "
            "dispatch_get_main_queue(), ^{\n"
            "        [weakSelf.interstitialAd loadAd];\n"
            "    });\n"
            "}\n\n"
            "#pragma mark - MAAdDelegate\n",
        ),
    ],
    "clean_lazy_ad_setup": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "@property (nonatomic, strong) MAInterstitialAd *interstitialAd;\n",
            "@property (nonatomic, copy) NSString *adUnitIdentifier;\n"
            "@property (nonatomic, strong) MAInterstitialAd *interstitialAd;\n",
        ),
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "        _interstitialAd = [[MAInterstitialAd alloc] "
            "initWithAdUnitIdentifier:adUnitIdentifier];\n"
            "        _interstitialAd.delegate = self;\n",
            "        _adUnitIdentifier = [adUnitIdentifier copy];\n",
        ),
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)load\n",
            "- (MAInterstitialAd *)interstitialAd\n"
            "{\n"
            "    if ( !_interstitialAd )\n"
            "    {\n"
            "        _interstitialAd = [[MAInterstitialAd alloc] "
            "initWithAdUnitIdentifier:self.adUnitIdentifier];\n"
            "        _interstitialAd.delegate = self;\n"
            "    }\n"
            "    return _interstitialAd;\n"
            "}\n\n"
            "- (void)load\n",
        ),
    ],
    "clean_ump_consent": [
        ADD_UMP_POD,
        Edit(
            OBJC_AD_MANAGER,
            "#import <AppLovinSDK/AppLovinSDK.h>\n",
            "#import <AppLovinSDK/AppLovinSDK.h>\n"
            "#import <AppTrackingTransparency/AppTrackingTransparency.h>\n"
            "#import <UserMessagingPlatform/UserMessagingPlatform.h>\n",
        ),
        Edit(OBJC_AD_MANAGER, "- (void)initializeSdk\n{\n" + OBJC_NO_PRIVACY_FLOW, OBJC_UMP_INIT),
    ],
    "clean_init_via_bootstrap": [
        Edit(OBJC_APP_DELEGATE, '#import "AdManager.h"\n', '#import "AppBootstrap.h"\n'),
        Edit(
            OBJC_APP_DELEGATE,
            "    [[AdManager sharedManager] initializeSdk];\n",
            "    [AppBootstrap startWithLaunchOptions:launchOptions];\n",
        ),
        WriteFile("PuzzleQuest/AppBootstrap.h", OBJC_BOOTSTRAP_H),
        WriteFile("PuzzleQuest/AppBootstrap.m", OBJC_BOOTSTRAP),
    ],
    "decoy_commented_load": [
        Edit(
            OBJC_AD_MANAGER,
            "        [self.interstitial load];\n",
            "        // [self.interstitial load];\n",
        ),
    ],
    "decoy_dead_reload": [
        Edit(
            f"{OBJC_INTERSTITIAL}.m",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self.interstitialAd loadAd];\n}",
            "- (void)didHideAd:(MAAd *)ad {}\n\n"
            "- (void)reloadAfterHide\n{\n    [self.interstitialAd loadAd];\n}",
        ),
    ],
    "decoy_sample_code": [
        *OBJC_DEFECTS["mediation_provider_missing"],
        WriteFile("Samples/MAXQuickStart/AppDelegate.m", OBJC_QUICK_START_SAMPLE),
    ],
    "multi_init_config": combine(
        OBJC_DEFECTS, "sdk_key_missing", "mediation_provider_missing", "cmp_missing"
    ),
    "multi_ad_lifecycle": combine(
        OBJC_DEFECTS, "ad_delegate_missing", "ad_reload_missing_on_display_fail"
    ),
    "large_clean": objc_game_code(),
    "large_rewarded_reload_missing_on_hide": [
        *objc_game_code(),
        Edit(
            f"{OBJC_REWARDED}.m",
            "- (void)didHideAd:(MAAd *)ad\n{\n    [self.rewardedAd loadAd];\n}",
            "- (void)didHideAd:(MAAd *)ad {}",
        ),
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
            (fixture / file).parent.mkdir(parents=True, exist_ok=True)
            (fixture / file).write_text(content, encoding="utf-8")
        case DeleteFile(file):
            (fixture / file).unlink()
        case DeletePlistKey(key):
            path = fixture / INFO_PLIST
            data = plistlib.loads(path.read_bytes())
            del data[key]
            path.write_bytes(plistlib.dumps(data))


def generate_xcode_project(fixture: Path) -> None:
    """
    Uses the fixture's own `project.yml` if a change wrote one, else `PROJECT_YML`.
    """
    spec = fixture / "project.yml"
    if not spec.exists():
        spec.write_text(PROJECT_YML, encoding="utf-8")
    try:
        subprocess.run(
            ["xcodegen", "generate", "--quiet", "--spec", str(spec)], check=True, cwd=fixture
        )
    finally:
        spec.unlink()


if __name__ == "__main__":
    main()
