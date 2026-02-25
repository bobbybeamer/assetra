import Foundation

struct TokenPair: Codable {
    let access: String
    let refresh: String
}

protocol TokenStore {
    func save(_ tokens: TokenPair)
    func load() -> TokenPair?
}

final class InMemoryTokenStore: TokenStore {
    private var tokens: TokenPair?

    func save(_ tokens: TokenPair) {
        self.tokens = tokens
    }

    func load() -> TokenPair? {
        tokens
    }
}

struct AuthClient {
    let baseURL: URL

    func login(username: String, password: String) async throws -> TokenPair {
        let url = baseURL.appendingPathComponent("/api/v1/auth/token/")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = ["username": username, "password": password]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode >= 400 {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(TokenPair.self, from: data)
    }

    func refresh(refreshToken: String) async throws -> TokenPair {
        let url = baseURL.appendingPathComponent("/api/v1/auth/token/refresh/")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = ["refresh": refreshToken]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode >= 400 {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(TokenPair.self, from: data)
    }
}

// Example usage (wire into your auth flow).
//
// let auth = AuthClient(baseURL: URL(string: "https://api.assetra.example")!)
// let tokens = try await auth.login(username: "user", password: "pass")
// tokenStore.save(tokens)
// let refreshed = try await auth.refresh(refreshToken: tokens.refresh)
// tokenStore.save(refreshed)
