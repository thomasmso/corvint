import Foundation

/// Soft currency earned in levels and the shop.
final class CoinsStore {
    static let shared = CoinsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.coins"

    var balance: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
