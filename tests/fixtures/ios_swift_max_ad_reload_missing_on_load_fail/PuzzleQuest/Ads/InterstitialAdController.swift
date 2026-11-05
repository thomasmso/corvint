import AppLovinSDK
import Foundation

final class InterstitialAdController: NSObject, MAAdDelegate {
    private let interstitialAd: MAInterstitialAd
    private var retryAttempt = 0.0

    init(adUnitIdentifier: String) {
        interstitialAd = MAInterstitialAd(adUnitIdentifier: adUnitIdentifier)
        super.init()
        interstitialAd.delegate = self
    }

    func load() {
        interstitialAd.load()
    }

    func showIfReady() {
        if interstitialAd.isReady {
            interstitialAd.show()
        }
    }

    // MARK: MAAdDelegate

    func didLoad(_ ad: MAAd) {
        retryAttempt = 0
    }

    func didFailToLoadAd(forAdUnitIdentifier adUnitIdentifier: String, withError error: MAError) {
        print("Interstitial failed to load: \(error.message)")
    }

    func didDisplay(_ ad: MAAd) {}

    func didClick(_ ad: MAAd) {}

    func didHide(_ ad: MAAd) {
        interstitialAd.load()
    }

    func didFail(toDisplay ad: MAAd, withError error: MAError) {
        interstitialAd.load()
    }
}
