import AppLovinSDK
import Foundation

final class RewardedAdController: NSObject, MARewardedAdDelegate {
    private let rewardedAd: MARewardedAd
    private var retryAttempt = 0.0
    private var onReward: ((MAReward) -> Void)?

    init(adUnitIdentifier: String) {
        rewardedAd = MARewardedAd.shared(withAdUnitIdentifier: adUnitIdentifier)
        super.init()
        rewardedAd.delegate = self
    }

    func load() {
        rewardedAd.load()
    }

    func showIfReady(onReward: @escaping (MAReward) -> Void) {
        guard rewardedAd.isReady else { return }
        self.onReward = onReward
        rewardedAd.show()
    }

    // MARK: MAAdDelegate

    func didLoad(_ ad: MAAd) {
        retryAttempt = 0
    }

    func didFailToLoadAd(forAdUnitIdentifier adUnitIdentifier: String, withError error: MAError) {
        // Retry with exponentially higher delays, up to 64 seconds
        retryAttempt += 1
        let delaySec = pow(2.0, min(6.0, retryAttempt))
        DispatchQueue.main.asyncAfter(deadline: .now() + delaySec) { [weak self] in
            self?.rewardedAd.load()
        }
    }

    func didDisplay(_ ad: MAAd) {}

    func didClick(_ ad: MAAd) {}

    func didHide(_ ad: MAAd) {}

    func didFail(toDisplay ad: MAAd, withError error: MAError) {
        rewardedAd.load()
    }

    // MARK: MARewardedAdDelegate

    func didRewardUser(for ad: MAAd, with reward: MAReward) {
        onReward?(reward)
        onReward = nil
    }
}
