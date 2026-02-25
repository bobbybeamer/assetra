import SwiftUI

struct ConflictResolutionView: View {
    @State private var conflicts: [ConflictRecord] = []
    private let store: InMemoryLocalStore

    init(store: InMemoryLocalStore = SampleStoreHolder.sharedStore) {
        self.store = store
    }

    var body: some View {
        List {
            ForEach(conflicts) { conflict in
                VStack(alignment: .leading, spacing: 6) {
                    Text("Asset \(conflict.assetId) (\(conflict.field))")
                        .font(.headline)
                    Text("Local: \(conflict.localValue)")
                    Text("Server: \(conflict.serverValue)")
                    Text("Updated: \(conflict.updatedAt)")
                        .font(.footnote)
                        .foregroundColor(.secondary)

                    HStack {
                        Button("Accept Server") {
                            Task {
                                await store?.resolveConflict(conflictId: conflict.id, useServerValue: true)
                                conflicts.removeAll { $0.id == conflict.id }
                            }
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Keep Local") {
                            Task {
                                await store?.resolveConflict(conflictId: conflict.id, useServerValue: false)
                                conflicts.removeAll { $0.id == conflict.id }
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("Conflicts")
        .task {
            conflicts = await store.pendingConflicts()
        }
    }
}

#Preview {
    NavigationView {
        ConflictResolutionView(store: SampleStoreHolder.sharedStore)
    }
}
