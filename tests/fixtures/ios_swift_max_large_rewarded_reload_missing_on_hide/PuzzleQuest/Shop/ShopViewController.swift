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
