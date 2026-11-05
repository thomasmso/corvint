import Foundation

/// Tile skins unlocked.
final class SkinsStore {
    static let shared = SkinsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.skins"

    var unlocked: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
