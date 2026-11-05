import Foundation

/// Furthest tutorial step the player has seen.
final class TutorialStore {
    static let shared = TutorialStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.tutorial"

    var step: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
