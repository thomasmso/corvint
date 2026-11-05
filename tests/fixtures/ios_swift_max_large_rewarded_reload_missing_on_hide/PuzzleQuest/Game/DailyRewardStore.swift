import Foundation

/// Day number of the last claimed daily reward.
final class DailyRewardStore {
    static let shared = DailyRewardStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.daily_reward"

    var lastClaimDay: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
