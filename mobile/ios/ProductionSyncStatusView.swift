import SwiftUI

struct ProductionSyncStatusView: View {
    @State private var baseUrl = "https://api.assetra.example"
    @State private var tenantId = "1"
    @State private var username = ""
    @State private var password = ""

    @State private var pendingCount = 0
    @State private var conflictCount = 0
    @State private var lastSyncAt = "Never"
    @State private var status = "Idle"

    private let localStore = SampleStoreHolder.sharedStore

    var body: some View {
        VStack(spacing: 12) {
            TextField("Base URL", text: $baseUrl)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .textFieldStyle(.roundedBorder)

            TextField("Tenant ID", text: $tenantId)
                .textFieldStyle(.roundedBorder)

            TextField("Username", text: $username)
                .textFieldStyle(.roundedBorder)

            SecureField("Password", text: $password)
                .textFieldStyle(.roundedBorder)

            Button("Refresh Status") {
                Task { await refreshStatus() }
            }

            Button("Retry Sync") {
                Task {
                    status = "Running..."
                    do {
                        try await SampleAppRunner.runSyncOnly(
                            baseURL: URL(string: baseUrl)!,
                            tenantId: tenantId,
                            username: username,
                            password: password
                        )
                        status = "Sync completed"
                    } catch {
                        status = "Sync failed: \(error.localizedDescription)"
                    }
                    await refreshStatus()
                }
            }

            Text("Pending queue: \(pendingCount)")
                .font(.footnote)
                .foregroundColor(.secondary)

            Text("Pending conflicts: \(conflictCount)")
                .font(.footnote)
                .foregroundColor(.secondary)

            Text("Last sync at: \(lastSyncAt)")
                .font(.footnote)
                .foregroundColor(.secondary)

            Text(status)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .navigationTitle("Sync Status")
        .task {
            await refreshStatus()
        }
    }

    private func refreshStatus() async {
        let pending = await localStore.pendingScanEvents()
        let conflicts = await localStore.pendingConflicts()
        let last = await localStore.lastSyncAt()

        pendingCount = pending.count
        conflictCount = conflicts.count
        lastSyncAt = last ?? "Never"
    }
}

#Preview {
    NavigationView {
        ProductionSyncStatusView()
    }
}
