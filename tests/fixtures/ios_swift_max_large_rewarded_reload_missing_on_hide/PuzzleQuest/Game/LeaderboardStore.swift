import Foundation

/// Best score submitted to the leaderboard.
final class LeaderboardStore {
    static let shared = LeaderboardStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.leaderboard"

    var bestScore: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
