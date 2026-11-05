import AppLovinSDK
import Foundation

// TODO: add the SDK key before release
private let sdkKey = ""

final class AdManager {
    static let shared = AdManager()

    private(set) var interstitial: InterstitialAdController?
    private(set) var rewarded: RewardedAdController?
    private var isInitialized = false
    private var readyHandlers: [() -> Void] = []

    func initializeSdk() {
        let settings = ALSdk.shared().settings
        settings.termsAndPrivacyPolicyFlowSettings.isEnabled = true
        settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = URL(string: "https://puzzlequest.example.com/privacy")
        settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = URL(string: "https://puzzlequest.example.com/terms")

        let initConfig = ALSdkInitializationConfiguration(sdkKey: sdkKey) { builder in
            builder.testDeviceAdvertisingIdentifiers = []
        }

        ALSdk.shared().initialize(with: initConfig) { _ in
            self.isInitialized = true

            let interstitial = InterstitialAdController(adUnitIdentifier: "c4f7e9a1b2d30658")
            interstitial.load()
            self.interstitial = interstitial

            let rewarded = RewardedAdController(adUnitIdentifier: "9e2b6d4f1a7c8035")
            rewarded.load()
            self.rewarded = rewarded

            self.readyHandlers.forEach { $0() }
            self.readyHandlers.removeAll()
        }
    }

    /// Runs `handler` once the SDK is initialized (immediately if it already is).
    func whenReady(_ handler: @escaping () -> Void) {
        if isInitialized {
            handler()
        } else {
            readyHandlers.append(handler)
        }
    }
}
