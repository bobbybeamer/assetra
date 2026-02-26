package com.assetra.sync

import java.time.Instant
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class LocalScanEvent(
    val clientEventId: String,
    val symbology: String,
    val rawValue: String,
    val sourceType: String,
    val capturedAt: String,
    val synced: Boolean,
)

interface SyncApi {
    suspend fun pushPull(
        lastSyncAt: String?,
        scanEvents: List<LocalScanEvent>,
        conflictAcknowledgements: List<ConflictAcknowledgement>,
    ): SyncResponse
}

data class SyncResponse(
    val serverTime: String,
    val acceptedScanEventIds: List<Int>,
    val assetChanges: List<Map<String, Any?>>,
    val conflicts: List<ConflictRecord>,
    val conflictStrategy: String,
)

class OfflineSyncEngine(
    private val localStore: LocalStore,
    private val syncApi: SyncApi,
) {
    suspend fun sync() = withContext(Dispatchers.IO) {
        val pending = localStore.pendingScanEvents()
        val pendingAcks = localStore.pendingConflictAcks()
        val response = syncApi.pushPull(localStore.lastSyncAt(), pending, pendingAcks)
        localStore.markSynced(pending.map { it.clientEventId })
        localStore.markConflictAcksSynced(pendingAcks.map { it.conflictId })
        localStore.upsertAssets(response.assetChanges)
        localStore.saveConflicts(response.conflicts)
        localStore.saveLastSyncAt(response.serverTime)
    }
}

interface LocalStore {
    suspend fun pendingScanEvents(): List<LocalScanEvent>
    suspend fun markSynced(clientEventIds: List<String>)
    suspend fun upsertAssets(assets: List<Map<String, Any?>>)
    suspend fun saveConflicts(conflicts: List<ConflictRecord>)
    suspend fun pendingConflicts(): List<ConflictRecord>
    suspend fun resolveConflict(conflictId: String, useServerValue: Boolean)
    suspend fun pendingConflictAcks(): List<ConflictAcknowledgement>
    suspend fun markConflictAcksSynced(conflictIds: List<String>)
    suspend fun saveLastSyncAt(serverTime: String)
    suspend fun lastSyncAt(): String?
}

class InMemoryLocalStore : LocalStore {
    private val events = mutableListOf<LocalScanEvent>()
    private val assets = mutableMapOf<String, Map<String, Any?>>()
    private val conflicts = mutableListOf<ConflictRecord>()
    private val conflictAcks = mutableListOf<ConflictAcknowledgement>()
    private var lastSync: String? = null

    override suspend fun pendingScanEvents(): List<LocalScanEvent> {
        return events.filter { !it.synced }
    }

    override suspend fun markSynced(clientEventIds: List<String>) {
        val updated = events.map { event ->
            if (clientEventIds.contains(event.clientEventId)) {
                event.copy(synced = true)
            } else {
                event
            }
        }
        events.clear()
        events.addAll(updated)
    }

    override suspend fun upsertAssets(assets: List<Map<String, Any?>>) {
        for (asset in assets) {
            val id = asset["id"]?.toString() ?: continue
            this.assets[id] = asset
        }
    }

    override suspend fun saveConflicts(conflicts: List<ConflictRecord>) {
        this.conflicts.addAll(conflicts)
    }

    override suspend fun pendingConflicts(): List<ConflictRecord> = conflicts.toList()

    override suspend fun resolveConflict(conflictId: String, useServerValue: Boolean) {
        val conflict = conflicts.firstOrNull { it.id == conflictId }
        if (!useServerValue && conflict != null) {
            val replayEvent = LocalScanEvent(
                clientEventId = UUID.randomUUID().toString(),
                symbology = "conflict_replay",
                rawValue = "asset=${conflict.assetId};field=${conflict.field};value=${conflict.localValue}",
                sourceType = "conflict_replay",
                capturedAt = Instant.now().toString(),
                synced = false,
            )
            events.add(replayEvent)

            val current = assets[conflict.assetId]?.toMutableMap() ?: mutableMapOf("id" to conflict.assetId)
            current[conflict.field] = conflict.localValue
            assets[conflict.assetId] = current
        }

        conflicts.removeAll { it.id == conflictId }
        conflictAcks.add(
            ConflictAcknowledgement(
                conflictId = conflictId,
                resolution = if (useServerValue) "accept_server" else "keep_local",
                resolvedAt = Instant.now().toString(),
            )
        )
    }

    override suspend fun pendingConflictAcks(): List<ConflictAcknowledgement> = conflictAcks.toList()

    override suspend fun markConflictAcksSynced(conflictIds: List<String>) {
        conflictAcks.removeAll { conflictIds.contains(it.conflictId) }
    }

    override suspend fun saveLastSyncAt(serverTime: String) {
        lastSync = serverTime
    }

    override suspend fun lastSyncAt(): String? = lastSync

    // Helper for demos to add local events.
    fun addLocalScanEvent(event: LocalScanEvent) {
        events.add(event)
    }

    // Helper for demos to seed conflict records.
    fun seedConflicts(seed: List<ConflictRecord>) {
        conflicts.clear()
        conflicts.addAll(seed)
    }
}

fun sampleCapture(localStore: InMemoryLocalStore, rawValue: String) {
    val event = LocalScanEvent(
        clientEventId = UUID.randomUUID().toString(),
        symbology = "qr",
        rawValue = rawValue,
        sourceType = "camera",
        capturedAt = Instant.now().toString(),
        synced = false,
    )
    localStore.addLocalScanEvent(event)
}

// Example usage (wire into your app lifecycle).
//
// val tokenProvider = object : AccessTokenProvider {
//     override fun accessToken(): String = currentAccessToken
//     override fun refreshAccessToken(): String {
//         val refreshed = authClient.refresh(currentRefreshToken)
//         currentAccessToken = refreshed.access
//         currentRefreshToken = refreshed.refresh
//         return currentAccessToken
//     }
// }
// val api = AssetraApi(
//     baseUrl = "https://api.assetra.example",
//     tenantId = "1",
//     tokenProvider = tokenProvider,
// )
// val localStore = InMemoryLocalStore()
// sampleCapture(localStore, rawValue = "QR-100")
// val engine = OfflineSyncEngine(localStore, api)
// engine.sync()
