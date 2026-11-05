import Foundation

/// Number of achievements unlocked.
final class AchievementsStore {
    static let shared = AchievementsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.achievements"

    var unlockedCount: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
