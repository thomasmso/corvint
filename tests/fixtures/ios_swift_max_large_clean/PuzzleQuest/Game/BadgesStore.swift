import Foundation

/// App icon badge count for unread notifications.
final class BadgesStore {
    static let shared = BadgesStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.badges"

    var count: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
