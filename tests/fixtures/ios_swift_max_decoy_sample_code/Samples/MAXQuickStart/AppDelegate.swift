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
