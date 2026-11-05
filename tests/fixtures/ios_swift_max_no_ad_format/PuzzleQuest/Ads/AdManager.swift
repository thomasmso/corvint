import AppLovinSDK
import Foundation

private let sdkKey = "UZeET0n1kyJYiCe32G9DNDD-Jj2-wRFBwZZiQR4gpHO2kkmADDMl7Ch91_vZKPuBoMOceI0RP0XCwGhWM7hnzj"

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
