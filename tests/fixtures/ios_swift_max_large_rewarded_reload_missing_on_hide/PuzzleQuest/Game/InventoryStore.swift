import Foundation

/// Number of items in the player's inventory.
final class InventoryStore {
    static let shared = InventoryStore()

    private let defaults = UserDefaults.standard
    private let key = "puzzlequest.inventory"

    var itemCount: Int {
        get { defaults.integer(forKey: key) }
        set { defaults.set(newValue, forKey: key) }
    }

    func reset() {
        defaults.removeObject(forKey: key)
    }
}
