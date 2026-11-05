import Foundation

/// Gifts from friends waiting to be opened.
final class GiftsStore {
    static let shared = GiftsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.gifts"

    var pending: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
