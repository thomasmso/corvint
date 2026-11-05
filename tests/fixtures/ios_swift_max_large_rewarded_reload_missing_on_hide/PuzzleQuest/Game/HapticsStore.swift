import Foundation

/// Haptic feedback intensity, 0 to 3.
final class HapticsStore {
    static let shared = HapticsStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.haptics"

    var intensity: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
