package com.assetra.sync

import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONArray
import org.json.JSONObject

interface AccessTokenProvider {
    fun accessToken(): String
    fun refreshAccessToken(): String
}

class AssetraApi(
    private val baseUrl: String,
    private val tenantId: String,
    private val tokenProvider: AccessTokenProvider,
) : SyncApi {
    override suspend fun pushPull(
        lastSyncAt: String?,
        scanEvents: List<LocalScanEvent>,
        conflictAcknowledgements: List<ConflictAcknowledgement>,
    ): SyncResponse {
        val url = URL("${baseUrl.trimEnd('/')}/api/v1/sync/")
        val payload = JSONObject()
        if (lastSyncAt != null) {
            payload.put("last_sync_at", lastSyncAt)
        }
        val scanArray = JSONArray()
        for (event in scanEvents) {
            val obj = JSONObject()
            obj.put("client_event_id", event.clientEventId)
            obj.put("symbology", event.symbology)
            obj.put("raw_value", event.rawValue)
            obj.put("source_type", event.sourceType)
            obj.put("captured_at", event.capturedAt)
            scanArray.put(obj)
        }
        payload.put("scan_events", scanArray)

        val ackArray = JSONArray()
        for (ack in conflictAcknowledgements) {
            val obj = JSONObject()
            obj.put("conflict_id", ack.conflictId)
            obj.put("resolution", ack.resolution)
            obj.put("resolved_at", ack.resolvedAt)
            ackArray.put(obj)
        }
        payload.put("conflict_acknowledgements", ackArray)

        var response = executeRequest(url, payload.toString(), tokenProvider.accessToken(), tenantId)
        if (response.first == 401) {
            val refreshedToken = tokenProvider.refreshAccessToken()
            response = executeRequest(url, payload.toString(), refreshedToken, tenantId)
        }

        if (response.first >= 400) {
            throw RuntimeException("Sync failed with status ${response.first}")
        }

        val responseJson = JSONObject(response.second)

        val acceptedArray = responseJson.optJSONArray("accepted_scan_event_ids") ?: JSONArray()
        val acceptedIds = (0 until acceptedArray.length()).map { acceptedArray.getInt(it) }

        val assetsArray = responseJson.optJSONArray("asset_changes") ?: JSONArray()
        val assetChanges = (0 until assetsArray.length()).map { index ->
            assetsArray.getJSONObject(index).toMap()
        }

        val conflictsArray = responseJson.optJSONArray("conflicts") ?: JSONArray()
        val conflicts = (0 until conflictsArray.length()).map { index ->
            val conflict = conflictsArray.getJSONObject(index)
            val assetId = conflict.optString("asset_id")
            val field = conflict.optString("field")
            val conflictId = conflict.optString("id").ifBlank { "${assetId}:${field}" }
            ConflictRecord(
                id = conflictId,
                assetId = assetId,
                field = field,
                localValue = conflict.optString("local_value"),
                serverValue = conflict.optString("server_value"),
                updatedAt = conflict.optString("updated_at"),
            )
        }

        return SyncResponse(
            serverTime = responseJson.optString("server_time"),
            acceptedScanEventIds = acceptedIds,
            assetChanges = assetChanges,
            conflicts = conflicts,
            conflictStrategy = responseJson.optString("conflict_strategy", "last-write-wins"),
        )
    }
}

private fun executeRequest(
    url: URL,
    payload: String,
    accessToken: String,
    tenantId: String,
): Pair<Int, String> {
    val connection = url.openConnection() as HttpURLConnection
    connection.requestMethod = "POST"
    connection.setRequestProperty("Content-Type", "application/json")
    connection.setRequestProperty("Authorization", "Bearer $accessToken")
    connection.setRequestProperty("X-Tenant-ID", tenantId)
    connection.doOutput = true

    connection.outputStream.use { stream ->
        stream.write(payload.toByteArray())
    }

    val status = connection.responseCode
    val bodyStream = if (status >= 400) connection.errorStream else connection.inputStream
    val responseText = bodyStream?.bufferedReader()?.use { it.readText() }.orEmpty()
    return status to responseText
}

private fun JSONObject.toMap(): Map<String, Any?> {
    val map = mutableMapOf<String, Any?>()
    val iterator = keys()
    while (iterator.hasNext()) {
        val key = iterator.next()
        map[key] = get(key)
    }
    return map
}
