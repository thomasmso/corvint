import SwiftUI

@main
struct PuzzleQuestApp: App {
    init() {
        AdManager.shared.initializeSdk()
    }

    var body: some Scene {
        WindowGroup {
            GameView()
                .ignoresSafeArea()
        }
    }
}

/// Hosts the UIKit game screen in SwiftUI.
struct GameView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> GameViewController {
        GameViewController()
    }

    func updateUIViewController(_ uiViewController: GameViewController, context: Context) {}
}
