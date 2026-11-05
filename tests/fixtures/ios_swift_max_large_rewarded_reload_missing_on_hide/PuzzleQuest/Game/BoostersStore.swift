import Foundation

/// Boosters the player owns.
final class BoostersStore {
    static let shared = BoostersStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.boosters"

    var owned: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
