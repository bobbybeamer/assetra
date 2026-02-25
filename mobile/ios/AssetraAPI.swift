import Foundation

protocol AccessTokenProvider {
    func accessToken() -> String
    func refreshAccessToken() async throws -> String
}

struct AssetraAPI: SyncAPI {
    let baseURL: URL
    let tenantId: String
    let tokenProvider: AccessTokenProvider

    func pushPull(
        lastSyncAt: String?,
        scanEvents: [LocalScanEvent],
        conflictAcknowledgements: [ConflictAcknowledgement]
    ) async throws -> SyncResponse {
        let url = baseURL.appendingPathComponent("/api/v1/sync/")
        let payload = SyncRequest(
            lastSyncAt: lastSyncAt,
            scanEvents: scanEvents,
            conflictAcknowledgements: conflictAcknowledgements
        )
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let body = try encoder.encode(payload)

        var response = try await executeRequest(
            url: url,
            body: body,
            accessToken: tokenProvider.accessToken(),
            tenantId: tenantId
        )
        if response.statusCode == 401 {
            let refreshedToken = try await tokenProvider.refreshAccessToken()
            response = try await executeRequest(
                url: url,
                body: body,
                accessToken: refreshedToken,
                tenantId: tenantId
            )
        }

        if response.statusCode >= 400 {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertToSnakeCase
        return try decoder.decode(SyncResponse.self, from: response.data)
    }
}

private struct SyncRequest: Codable {
    let lastSyncAt: String?
    let scanEvents: [LocalScanEvent]
    let conflictAcknowledgements: [ConflictAcknowledgement]
}

private func executeRequest(
    url: URL,
    body: Data,
    accessToken: String,
    tenantId: String
) async throws -> (statusCode: Int, data: Data) {
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
    request.setValue(tenantId, forHTTPHeaderField: "X-Tenant-ID")
    request.httpBody = body

    let (data, response) = try await URLSession.shared.data(for: request)
    let status = (response as? HTTPURLResponse)?.statusCode ?? 0
    return (status, data)
}
