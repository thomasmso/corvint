import AppLovinSDK
import UIKit

final class GameViewController: UIViewController, MAAdViewAdDelegate {
    private let playButton = UIButton(type: .system)
    private let hintButton = UIButton(type: .system)
    private var bannerView: MAAdView?
    private var hints = 3
    private var level = 1

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        playButton.setTitle("Play", for: .normal)
        playButton.addTarget(self, action: #selector(playTapped), for: .touchUpInside)
        hintButton.setTitle("Get a hint", for: .normal)
        hintButton.addTarget(self, action: #selector(hintTapped), for: .touchUpInside)

        let stack = UIStackView(arrangedSubviews: [playButton, hintButton])
        stack.axis = .vertical
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])

        AdManager.shared.whenReady { [weak self] in
            self?.attachBanner()
        }
    }

    @objc private func playTapped() {
        startLevel()
    }

    @objc private func hintTapped() {
        AdManager.shared.rewarded?.showIfReady { [weak self] _ in
            self?.hints += 1
        }
    }

    private func startLevel() {
        // Gameplay is out of scope for this fixture; finishing a level is simulated.
        levelCompleted()
    }

    private func levelCompleted() {
        level += 1
        AdManager.shared.interstitial?.showIfReady()
    }

    private func attachBanner() {
        let adView = MAAdView(adUnitIdentifier: "5a8c1e3f7b2d9046")
        adView.delegate = self
        adView.backgroundColor = .black
        adView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(adView)

        let height: CGFloat = UIDevice.current.userInterfaceIdiom == .pad ? 90 : 50
        NSLayoutConstraint.activate([
            adView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            adView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            adView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            adView.heightAnchor.constraint(equalToConstant: height),
        ])

        adView.loadAd()
        bannerView = adView
    }

    // MARK: MAAdViewAdDelegate (banners refresh automatically)

    func didLoad(_ ad: MAAd) {}

    func didFailToLoadAd(forAdUnitIdentifier adUnitIdentifier: String, withError error: MAError) {}

    func didClick(_ ad: MAAd) {}

    func didFail(toDisplay ad: MAAd, withError error: MAError) {}

    func didExpand(_ ad: MAAd) {}

    func didCollapse(_ ad: MAAd) {}

    func didDisplay(_ ad: MAAd) {}

    func didHide(_ ad: MAAd) {}
}
