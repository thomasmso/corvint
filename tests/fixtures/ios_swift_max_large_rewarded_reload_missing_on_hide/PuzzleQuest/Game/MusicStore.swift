import Foundation

/// Music volume, 0 to 100.
final class MusicStore {
    static let shared = MusicStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.music"

    var volume: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
