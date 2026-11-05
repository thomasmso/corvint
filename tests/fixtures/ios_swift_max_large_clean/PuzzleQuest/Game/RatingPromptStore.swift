import Foundation

/// Times the app rating prompt has been shown.
final class RatingPromptStore {
    static let shared = RatingPromptStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.rating_prompt"

    var timesShown: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
