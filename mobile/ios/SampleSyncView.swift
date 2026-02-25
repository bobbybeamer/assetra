import SwiftUI

struct SampleSyncView: View {
    @State private var baseUrl = "https://api.assetra.example"
    @State private var tenantId = "1"
    @State private var username = ""
    @State private var password = ""
    @State private var status = "Idle"
    @State private var showConflicts = false

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

            Button("Run Sync Sample") {
                Task {
                    status = "Running..."
                    do {
                        try await SampleAppRunner.runSample(
                            baseURL: URL(string: baseUrl)!,
                            tenantId: tenantId,
                            username: username,
                            password: password
                        )
                        status = "Sync completed"
                    } catch {
                        status = "Sync failed: \(error.localizedDescription)"
                    }
                }
            }

            Button("View Conflicts") {
                showConflicts = true
            }

            Text(status)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .sheet(isPresented: $showConflicts) {
            NavigationView {
                ConflictResolutionView(store: SampleStoreHolder.sharedStore)
            }
        }
    }
}

#Preview {
    SampleSyncView()
}
