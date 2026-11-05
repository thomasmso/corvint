import Foundation

/// Tiles cleared in total.
final class TilesStore {
    static let shared = TilesStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.tiles"

    var cleared: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
