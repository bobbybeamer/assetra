package com.assetra.auth

import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject


data class TokenPair(
    val access: String,
    val refresh: String,
)

interface TokenStore {
    fun save(tokens: TokenPair)
    fun load(): TokenPair?
}

class InMemoryTokenStore : TokenStore {
    private var tokens: TokenPair? = null

    override fun save(tokens: TokenPair) {
        this.tokens = tokens
    }

    override fun load(): TokenPair? = tokens
}

class AuthClient(private val baseUrl: String) {
    fun login(username: String, password: String): TokenPair {
        val url = URL("${baseUrl.trimEnd('/')}/api/v1/auth/token/")
        val payload = JSONObject()
        payload.put("username", username)
        payload.put("password", password)
        return postJson(url, payload)
    }

    fun refresh(refreshToken: String): TokenPair {
        val url = URL("${baseUrl.trimEnd('/')}/api/v1/auth/token/refresh/")
        val payload = JSONObject()
        payload.put("refresh", refreshToken)
        return postJson(url, payload)
    }

    private fun postJson(url: URL, payload: JSONObject): TokenPair {
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.setRequestProperty("Content-Type", "application/json")
        connection.doOutput = true

        connection.outputStream.use { stream ->
            stream.write(payload.toString().toByteArray())
        }

        val responseText = connection.inputStream.bufferedReader().use { it.readText() }
        val responseJson = JSONObject(responseText)
        return TokenPair(
            access = responseJson.getString("access"),
            refresh = responseJson.getString("refresh"),
        )
    }
}

// Example usage (wire into your auth flow).
//
// val auth = AuthClient(baseUrl = "https://api.assetra.example")
// val tokens = auth.login("user", "pass")
// tokenStore.save(tokens)
// val refreshed = auth.refresh(tokens.refresh)
// tokenStore.save(refreshed)
