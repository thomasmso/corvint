import Foundation

/// Reward chests not opened yet.
final class ChestsStore {
    static let shared = ChestsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.chests"

    var unopened: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
