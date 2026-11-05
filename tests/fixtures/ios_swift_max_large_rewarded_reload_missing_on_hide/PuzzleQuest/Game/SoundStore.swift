import Foundation

/// Sound effects volume, 0 to 100.
final class SoundStore {
    static let shared = SoundStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.sound"

    var volume: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
