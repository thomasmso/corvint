"""
MAX integration rules. The agent prompt and the evaluator share these ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RuleId = Literal[
    # AppLovin SDK integration
    "MAX-NOT-DETECTED",
    "MAX-SDK-OUTDATED",
    "MAX-INIT-MISSING",
    "MAX-MEDIATION-PROVIDER-MISSING",
    "MAX-SDK-KEY-MISSING",
    "MAX-INIT-NOT-AT-LAUNCH",
    # Configuration
    "MAX-SKADNETWORK-MISSING",
    # Ad load logic
    "MAX-NO-AD-FORMAT",
    "MAX-AD-LOAD-MISSING",
    "MAX-AD-DELEGATE-MISSING",
    "MAX-AD-RELOAD-MISSING",
    "MAX-LOAD-BEFORE-INIT",
    # Networks
    "MAX-NETWORK-MISSING",
    # Privacy
    "MAX-CMP-MISSING",
    # Anything else
    "MAX-OTHER",
]
Severity = Literal["info", "low", "medium", "high", "critical"]


@dataclass(frozen=True)
class Rule:
    rule_id: RuleId
    severity: Severity
    report_when: str
    do_not_report_when: str
    subject: str


RULES: tuple[Rule, ...] = (
    # --- AppLovin SDK integration ---
    Rule(
        "MAX-NOT-DETECTED",
        "info",
        "No MAX dependency or SDK usage was found.",
        "Any MAX dependency or SDK usage was found.",
        "platform",
    ),
    Rule(
        "MAX-SDK-OUTDATED",
        "medium",
        "inspect_app_project reports allows_latest_version false for AppLovinSDK: its Podfile "
        "constraint excludes latest_sdk_version.",
        "allows_latest_version is true or null. Never judge versions yourself.",
        "'AppLovinSDK'",
    ),
    Rule(
        "MAX-INIT-MISSING",
        "high",
        "MAX pods are present but project source never initializes the SDK "
        "(ALSdk.shared().initialize(with:...) in Swift, or the Objective-C equivalent).",
        "An initialization call exists anywhere in project source.",
        "'ios'",
    ),
    Rule(
        "MAX-MEDIATION-PROVIDER-MISSING",
        "medium",
        "The ALSdkInitializationConfiguration builder never sets "
        "builder.mediationProvider = ALMediationProviderMAX.",
        "The builder sets it, or the SDK is never initialized (MAX-INIT-MISSING covers that).",
        "'mediationProvider'",
    ),
    Rule(
        "MAX-SDK-KEY-MISSING",
        "high",
        "Neither the ALSdkInitializationConfiguration (sdkKey: argument) nor Info.plist "
        "(AppLovinSdkKey) provides a non-empty SDK key.",
        "Either provides a non-empty key. If the key comes from somewhere you cannot read "
        "(remote config, build settings), report with requires_manual_review instead.",
        "'sdkKey'",
    ),
    Rule(
        "MAX-INIT-NOT-AT-LAUNCH",
        "medium",
        "SDK initialization does not run at app launch: it is deferred to a screen, a button, "
        "login, a timer or a remote config result instead of being reached from "
        "application(_:didFinishLaunchingWithOptions:) or the SwiftUI App initializer.",
        "Initialization is called from launch, directly or through helpers. Static analysis "
        "only: never claim when it runs on a device.",
        "method that initializes",
    ),
    # --- Configuration ---
    Rule(
        "MAX-SKADNETWORK-MISSING",
        "high",
        "The app's Info.plist has no SKAdNetworkItems, or inspect_app_project lists "
        "missing_applovin_skadnetwork_ids for it.",
        "No AppLovin SKAdNetwork IDs are missing. Info.plist files of test targets or "
        "extensions do not count.",
        "Info.plist path",
    ),
    # --- Ad load logic ---
    Rule(
        "MAX-NO-AD-FORMAT",
        "high",
        "MAX is integrated but no ad format is: no MAInterstitialAd, MARewardedAd, MAAdView, "
        "MAAppOpenAd or MANativeAdLoader in project source.",
        "At least one ad format class is used.",
        "'ad formats'",
    ),
    Rule(
        "MAX-AD-LOAD-MISSING",
        "high",
        "An ad object is created but its first load (load() in Swift, loadAd in "
        "Objective-C) is never called, or only from callbacks that cannot fire before a load.",
        "A first load is reachable, e.g. from the initialization callback.",
        "ad format: 'interstitial', 'rewarded', 'banner', 'mrec', 'app open' or 'native'",
    ),
    Rule(
        "MAX-AD-DELEGATE-MISSING",
        "high",
        "An ad object never gets its delegate set (delegate = ... before loading).",
        "The delegate is set on that object.",
        "ad format: 'interstitial', 'rewarded', 'banner', 'mrec', 'app open' or 'native'",
    ),
    Rule(
        "MAX-AD-RELOAD-MISSING",
        "medium",
        "A full-screen ad (interstitial, rewarded, app open) does not load again in one of: "
        "didFailToLoadAd (retry, ideally with backoff), didFail(toDisplay:) or didHide. Report "
        "one finding per format, naming the callbacks missing a reload.",
        "Each of those callbacks reloads, directly or through a helper. Banners and MRECs "
        "refresh automatically: never report them.",
        "'<format>:<callbacks>', e.g. 'interstitial:didHide'",
    ),
    Rule(
        "MAX-LOAD-BEFORE-INIT",
        "medium",
        "An ad load or show call is reachable before the SDK initialization callback fires.",
        "Loads happen only from the initialization callback or code that runs after it.",
        "ad format or method name",
    ),
    # --- Networks ---
    Rule(
        "MAX-NETWORK-MISSING",
        "medium",
        "The Podfile lacks a baseline mediation adapter: AppLovinMediationGoogleAdapter "
        "(Google AdMob) or AppLovinMediationUnityAdsAdapter (Unity Ads). One finding per "
        "missing adapter.",
        "Both adapters are declared. Never claim revenue impact.",
        "'Google' or 'UnityAds'",
    ),
    # --- Privacy ---
    Rule(
        "MAX-CMP-MISSING",
        "medium",
        "No consent flow shows the ATT prompt: AppLovin's Terms and Privacy Policy flow is not "
        "enabled (termsAndPrivacyPolicyFlowSettings.isEnabled in code, or ConsentFlowEnabled in "
        "AppLovin-Settings.plist) and there is no other CMP (e.g. Google UMP: "
        "UMPConsentInformation) or ATTrackingManager.requestTrackingAuthorization call. Also "
        "report when such a flow exists but the app's Info.plist lacks "
        "NSUserTrackingUsageDescription.",
        "A flow is present and NSUserTrackingUsageDescription is set. Do not give legal opinions.",
        "'consent flow' or 'NSUserTrackingUsageDescription'",
    ),
    # --- Anything else ---
    Rule(
        "MAX-OTHER",
        "low",
        "A concrete MAX integration defect with direct evidence that no other rule covers.",
        "Style, generic best practices, privacy/legal opinions, or anything without evidence.",
        "short identifier",
    ),
)


def render_rule_catalog() -> str:
    return "\n".join(
        f"- {rule.rule_id} (default severity {rule.severity})\n"
        f"  Report when: {rule.report_when}\n"
        f"  Do not report when: {rule.do_not_report_when}\n"
        f"  subject: {rule.subject}"
        for rule in RULES
    )
