import Foundation

/// Lives left before the player must wait or refill.
final class LivesStore {
    static let shared = LivesStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.lives"

    var count: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
