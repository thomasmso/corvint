import Foundation

/// Consecutive days the player has opened the game.
final class StreakStore {
    static let shared = StreakStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.streak"

    var days: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
