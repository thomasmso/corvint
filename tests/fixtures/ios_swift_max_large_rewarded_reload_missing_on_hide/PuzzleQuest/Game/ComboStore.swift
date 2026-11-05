import Foundation

/// Longest combo the player has made.
final class ComboStore {
    static let shared = ComboStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.combo"

    var best: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
