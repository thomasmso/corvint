import Foundation

/// Puzzles solved across all modes.
final class PuzzlesStore {
    static let shared = PuzzlesStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.puzzles"

    var solved: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
