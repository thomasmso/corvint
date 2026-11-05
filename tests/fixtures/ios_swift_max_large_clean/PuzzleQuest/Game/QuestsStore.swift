import Foundation

/// Quests completed this season.
final class QuestsStore {
    static let shared = QuestsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.quests"

    var completed: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
