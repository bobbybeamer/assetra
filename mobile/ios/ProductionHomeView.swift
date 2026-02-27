import SwiftUI

struct ProductionHomeView: View {
    var body: some View {
        TabView {
            NavigationView {
                ProductionScanView()
            }
            .tabItem {
                Label("Scan", systemImage: "barcode.viewfinder")
            }

            NavigationView {
                ProductionSyncStatusView()
            }
            .tabItem {
                Label("Sync", systemImage: "arrow.triangle.2.circlepath")
            }
        }
    }
}

#Preview {
    ProductionHomeView()
}
