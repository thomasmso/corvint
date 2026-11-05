import Foundation

/// Stars earned across all levels.
final class StarsStore {
    static let shared = StarsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.stars"

    var total: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
