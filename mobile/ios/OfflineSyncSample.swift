import Foundation

struct LocalScanEvent: Codable {
    let clientEventId: String
    let symbology: String
    let rawValue: String
    let sourceType: String
    let capturedAt: String
    let synced: Bool
}

struct SyncResponse: Codable {
    let serverTime: String
    let acceptedScanEventIds: [Int]
    let assetChanges: [[String: JSONValue]]
    let conflicts: [ConflictRecord]
    let conflictStrategy: String
}

protocol SyncAPI {
    func pushPull(
        lastSyncAt: String?,
        scanEvents: [LocalScanEvent],
        conflictAcknowledgements: [ConflictAcknowledgement]
    ) async throws -> SyncResponse
}

protocol LocalStore {
    func pendingScanEvents() async -> [LocalScanEvent]
    func markSynced(clientEventIds: [String]) async
    func upsertAssets(_ assets: [[String: JSONValue]]) async
    func saveConflicts(_ conflicts: [ConflictRecord]) async
    func pendingConflicts() async -> [ConflictRecord]
    func resolveConflict(conflictId: String, useServerValue: Bool) async
    func pendingConflictAcks() async -> [ConflictAcknowledgement]
    func markConflictAcksSynced(conflictIds: [String]) async
    func saveLastSyncAt(_ value: String) async
    func lastSyncAt() async -> String?
}

final class InMemoryLocalStore: LocalStore {
    private var events: [LocalScanEvent] = []
    private var assets: [String: [String: JSONValue]] = [:]
    private var conflicts: [ConflictRecord] = []
    private var conflictAcks: [ConflictAcknowledgement] = []
    private var lastSync: String?

    func pendingScanEvents() async -> [LocalScanEvent] {
        events.filter { !$0.synced }
    }

    func markSynced(clientEventIds: [String]) async {
        events = events.map { event in
            if clientEventIds.contains(event.clientEventId) {
                return LocalScanEvent(
                    clientEventId: event.clientEventId,
                    symbology: event.symbology,
                    rawValue: event.rawValue,
                    sourceType: event.sourceType,
                    capturedAt: event.capturedAt,
                    synced: true
                )
            }
            return event
        }
    }

    func upsertAssets(_ assets: [[String: JSONValue]]) async {
        for asset in assets {
            if case let .string(id)? = asset["id"] {
                self.assets[id] = asset
            } else if case let .number(id)? = asset["id"] {
                self.assets[String(id)] = asset
            }
        }
    }

    func saveConflicts(_ conflicts: [ConflictRecord]) async {
        self.conflicts.append(contentsOf: conflicts)
    }

    func pendingConflicts() async -> [ConflictRecord] {
        conflicts
    }

    func resolveConflict(conflictId: String, useServerValue: Bool) async {
        if !useServerValue, let conflict = conflicts.first(where: { $0.id == conflictId }) {
            let replayEvent = LocalScanEvent(
                clientEventId: UUID().uuidString,
                symbology: "conflict_replay",
                rawValue: "asset=\(conflict.assetId);field=\(conflict.field);value=\(conflict.localValue)",
                sourceType: "conflict_replay",
                capturedAt: ISO8601DateFormatter().string(from: Date()),
                synced: false
            )
            events.append(replayEvent)

            var current = assets[conflict.assetId] ?? ["id": .string(conflict.assetId)]
            current[conflict.field] = .string(conflict.localValue)
            assets[conflict.assetId] = current
        }

        conflicts.removeAll { $0.id == conflictId }
        conflictAcks.append(
            ConflictAcknowledgement(
                conflictId: conflictId,
                resolution: useServerValue ? "accept_server" : "keep_local",
                resolvedAt: ISO8601DateFormatter().string(from: Date())
            )
        )
    }

    func pendingConflictAcks() async -> [ConflictAcknowledgement] {
        conflictAcks
    }

    func markConflictAcksSynced(conflictIds: [String]) async {
        conflictAcks.removeAll { conflictIds.contains($0.conflictId) }
    }

    func saveLastSyncAt(_ value: String) async {
        lastSync = value
    }

    func lastSyncAt() async -> String? {
        lastSync
    }

    // Helper for demos to add local events.
    func addLocalScanEvent(_ event: LocalScanEvent) {
        events.append(event)
    }

    // Helper for demos to seed conflict records.
    func seedConflicts(_ seed: [ConflictRecord]) {
        conflicts = seed
    }
}

func sampleCapture(localStore: InMemoryLocalStore, rawValue: String) {
    let formatter = ISO8601DateFormatter()
    let event = LocalScanEvent(
        clientEventId: UUID().uuidString,
        symbology: "qr",
        rawValue: rawValue,
        sourceType: "camera",
        capturedAt: formatter.string(from: Date()),
        synced: false
    )
    localStore.addLocalScanEvent(event)
}

final class OfflineSyncEngine {
    private let store: LocalStore
    private let api: SyncAPI

    init(store: LocalStore, api: SyncAPI) {
        self.store = store
        self.api = api
    }

    func sync() async throws {
        let pending = await store.pendingScanEvents()
        let pendingAcks = await store.pendingConflictAcks()
        let response = try await api.pushPull(
            lastSyncAt: await store.lastSyncAt(),
            scanEvents: pending,
            conflictAcknowledgements: pendingAcks
        )
        await store.markSynced(clientEventIds: pending.map { $0.clientEventId })
        await store.markConflictAcksSynced(conflictIds: pendingAcks.map { $0.conflictId })
        await store.upsertAssets(response.assetChanges)
        await store.saveConflicts(response.conflicts)
        await store.saveLastSyncAt(response.serverTime)
    }
}

// Example usage (wire into your app lifecycle).
//
// struct TokenProvider: AccessTokenProvider {
//     var access: String
//     var refresh: String
//     let authClient: AuthClient
//
//     func accessToken() -> String { access }
//
//     func refreshAccessToken() async throws -> String {
//         let tokens = try await authClient.refresh(refreshToken: refresh)
//         // Persist tokens in your store as needed.
//         return tokens.access
//     }
// }
// let api = AssetraAPI(
//     baseURL: URL(string: "https://api.assetra.example")!,
//     tenantId: "1",
//     tokenProvider: tokenProvider
// )
// let localStore = InMemoryLocalStore()
// sampleCapture(localStore: localStore, rawValue: "QR-100")
// let engine = OfflineSyncEngine(store: localStore, api: api)
// Task { try await engine.sync() }
