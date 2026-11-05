import Foundation

/// Highest level the player has unlocked.
final class LevelStore {
    static let shared = LevelStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.level"

    var current: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
