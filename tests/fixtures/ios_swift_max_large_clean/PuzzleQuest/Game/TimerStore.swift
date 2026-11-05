import Foundation

/// Fastest level completion, in seconds.
final class TimerStore {
    static let shared = TimerStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.timer"

    var bestSeconds: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
