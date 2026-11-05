import Foundation

/// Index of the selected board theme.
final class ThemeStore {
    static let shared = ThemeStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.theme"

    var selectedIndex: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
