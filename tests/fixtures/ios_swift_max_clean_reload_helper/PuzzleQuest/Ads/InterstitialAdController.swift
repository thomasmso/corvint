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

    private func loadNextAd(after delaySec: Double = 0) {
        DispatchQueue.main.asyncAfter(deadline: .now() + delaySec) { [weak self] in
            self?.interstitialAd.load()
        }
    }

    // MARK: MAAdDelegate

    func didLoad(_ ad: MAAd) {
        retryAttempt = 0
    }

    func didFailToLoadAd(forAdUnitIdentifier adUnitIdentifier: String, withError error: MAError) {
        // Retry with exponentially higher delays, up to 64 seconds
        retryAttempt += 1
        loadNextAd(after: pow(2.0, min(6.0, retryAttempt)))
    }

    func didDisplay(_ ad: MAAd) {}

    func didClick(_ ad: MAAd) {}

    func didHide(_ ad: MAAd) {
        loadNextAd()
    }

    func didFail(toDisplay ad: MAAd, withError error: MAError) {
        loadNextAd()
    }
}
