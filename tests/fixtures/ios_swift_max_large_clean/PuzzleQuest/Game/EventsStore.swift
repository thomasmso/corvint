import Foundation

/// Live events the player has joined.
final class EventsStore {
    static let shared = EventsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.events"

    var activeCount: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
