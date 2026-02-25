import Foundation

final class SampleTokenProvider: AccessTokenProvider {
    private let authClient: AuthClient
    private let tokenStore: InMemoryTokenStore

    init(authClient: AuthClient, tokenStore: InMemoryTokenStore) {
        self.authClient = authClient
        self.tokenStore = tokenStore
    }

    func accessToken() -> String {
        tokenStore.load()?.access ?? ""
    }

    func refreshAccessToken() async throws -> String {
        let current = tokenStore.load()
        let refreshed = try await authClient.refresh(refreshToken: current?.refresh ?? "")
        tokenStore.save(refreshed)
        return refreshed.access
    }
}

enum SampleAppRunner {
    static func runSample(baseURL: URL, tenantId: String, username: String, password: String) async throws {
        let authClient = AuthClient(baseURL: baseURL)
        let tokenStore = InMemoryTokenStore()

        let initial = try await authClient.login(username: username, password: password)
        tokenStore.save(initial)

        let tokenProvider = SampleTokenProvider(authClient: authClient, tokenStore: tokenStore)
        let api = AssetraAPI(baseURL: baseURL, tenantId: tenantId, tokenProvider: tokenProvider)
        let localStore = SampleStoreHolder.sharedStore

        sampleCapture(localStore: localStore, rawValue: "QR-100")

        let engine = OfflineSyncEngine(store: localStore, api: api)
        try await engine.sync()
    }
}

// Example usage (run from a test harness or app lifecycle):
//
// Task {
//     try await SampleAppRunner.runSample(
//         baseURL: URL(string: "https://api.assetra.example")!,
//         tenantId: "1",
//         username: "user",
//         password: "pass"
//     )
// }
