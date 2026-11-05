import Foundation

/// Current season pass tier.
final class SeasonPassStore {
    static let shared = SeasonPassStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.season_pass"

    var tier: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
