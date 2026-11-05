import Foundation

/// Number of app sessions.
final class SessionsStore {
    static let shared = SessionsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.sessions"

    var count: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
