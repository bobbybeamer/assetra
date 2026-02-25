package com.assetra.sample

import com.assetra.auth.AuthClient
import com.assetra.auth.InMemoryTokenStore
import com.assetra.auth.TokenPair
import com.assetra.sync.AccessTokenProvider
import com.assetra.sync.AssetraApi
import com.assetra.sync.OfflineSyncEngine
import com.assetra.sync.SampleStoreHolder
import com.assetra.sync.sampleCapture
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext

class SampleTokenProvider(
    private val authClient: AuthClient,
    private val tokenStore: InMemoryTokenStore,
) : AccessTokenProvider {
    override fun accessToken(): String = tokenStore.load()?.access ?: ""

    override fun refreshAccessToken(): String {
        val current = tokenStore.load() ?: return ""
        val refreshed = authClient.refresh(current.refresh)
        tokenStore.save(refreshed)
        return refreshed.access
    }
}

object SampleAppRunner {
    fun runSample(baseUrl: String, tenantId: String, username: String, password: String) = runBlocking {
        val authClient = AuthClient(baseUrl)
        val tokenStore = InMemoryTokenStore()

        val initial: TokenPair = withContext(Dispatchers.IO) {
            authClient.login(username, password)
        }
        tokenStore.save(initial)

        val tokenProvider = SampleTokenProvider(authClient, tokenStore)
        val api = AssetraApi(
            baseUrl = baseUrl,
            tenantId = tenantId,
            tokenProvider = tokenProvider,
        )

        val localStore = SampleStoreHolder.store
        sampleCapture(localStore, rawValue = "QR-100")

        val engine = OfflineSyncEngine(localStore, api)
        engine.sync()
    }
}

// Example usage (run from a test harness or Android Activity):
//
// SampleAppRunner.runSample(
//     baseUrl = "https://api.assetra.example",
//     tenantId = "1",
//     username = "user",
//     password = "pass"
// )
