import Foundation

/// Hints the player can spend on a puzzle.
final class HintsStore {
    static let shared = HintsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.hints"

    var remaining: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
