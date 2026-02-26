package com.assetra.scan

import java.util.UUID

interface ScanProvider {
    val name: String
    fun start(onResult: (ScanResult) -> Unit)
    fun stop()
}

data class ScanResult(
    val symbology: String,
    val rawValue: String,
    val sourceType: String,
)

interface ScannerBackend {
    val backendName: String
    fun isAvailable(): Boolean
    fun start(onResult: (ScanResult) -> Unit)
    fun stop()
}

interface CameraScanSession {
    fun start(onDecoded: (symbology: String, rawValue: String) -> Unit)
    fun stop()
}

interface DataWedgeSession {
    fun start(onIntentPayload: (Map<String, String>) -> Unit)
    fun stop()
}

class MlKitCameraBackend(
    private val session: CameraScanSession? = null,
) : ScannerBackend {
    override val backendName: String = "mlkit"

    override fun isAvailable(): Boolean {
        return session != null
    }

    override fun start(onResult: (ScanResult) -> Unit) {
        val activeSession = session ?: return
        activeSession.start { symbology, rawValue ->
            onResult(
                ScanResult(
                    symbology = symbology.ifBlank { "unknown" },
                    rawValue = rawValue,
                    sourceType = "camera",
                )
            )
        }
    }

    override fun stop() {
        session?.stop()
    }
}

class DataWedgeEnterpriseBackend(
    private val session: DataWedgeSession? = null,
) : ScannerBackend {
    override val backendName: String = "datawedge"

    override fun isAvailable(): Boolean {
        return session != null
    }

    override fun start(onResult: (ScanResult) -> Unit) {
        val activeSession = session ?: return
        activeSession.start { payload ->
            parseDataWedgePayload(payload)?.let(onResult)
        }
    }

    override fun stop() {
        session?.stop()
    }
}

fun parseDataWedgePayload(payload: Map<String, String>): ScanResult? {
    val rawValue = payload["com.symbol.datawedge.data_string"] ?: payload["data_string"] ?: return null
    val labelType = payload["com.symbol.datawedge.label_type"] ?: payload["label_type"] ?: "unknown"

    return ScanResult(
        symbology = labelType,
        rawValue = rawValue,
        sourceType = "enterprise_scanner",
    )
}

private fun selectBackend(backends: List<ScannerBackend>): ScannerBackend? {
    return backends.firstOrNull { it.isAvailable() } ?: backends.firstOrNull()
}

private class NoOpBackend(
    override val backendName: String,
    private val defaultSource: String,
) : ScannerBackend {
    override fun isAvailable(): Boolean = true

    override fun start(onResult: (ScanResult) -> Unit) {
        onResult(
            ScanResult(
                symbology = "demo",
                rawValue = "${backendName}_${UUID.randomUUID()}",
                sourceType = defaultSource,
            )
        )
    }

    override fun stop() {
    }
}

class CameraScanProvider(
    private val backends: List<ScannerBackend> = listOf(
        MlKitCameraBackend(),
        NoOpBackend(backendName = "camera_fallback", defaultSource = "camera")
    )
) : ScanProvider {
    override val name: String = "camera"
    private var activeBackend: ScannerBackend? = null

    override fun start(onResult: (ScanResult) -> Unit) {
        stop()
        val backend = selectBackend(backends) ?: return
        activeBackend = backend
        backend.start { result ->
            onResult(result.copy(sourceType = name))
        }
    }

    override fun stop() {
        activeBackend?.stop()
        activeBackend = null
    }
}

class RfidScanProvider(
    private val backends: List<ScannerBackend> = listOf(
        NoOpBackend(backendName = "rfid_stub", defaultSource = "rfid")
    )
) : ScanProvider {
    override val name: String = "rfid"
    private var activeBackend: ScannerBackend? = null

    override fun start(onResult: (ScanResult) -> Unit) {
        stop()
        val backend = selectBackend(backends) ?: return
        activeBackend = backend
        backend.start { result ->
            onResult(result.copy(sourceType = name))
        }
    }

    override fun stop() {
        activeBackend?.stop()
        activeBackend = null
    }
}

class EnterpriseScannerProvider(
    private val backends: List<ScannerBackend> = listOf(
        DataWedgeEnterpriseBackend(),
        NoOpBackend(backendName = "intent_scanner_stub", defaultSource = "enterprise_scanner")
    )
) : ScanProvider {
    override val name: String = "enterprise_scanner"
    private var activeBackend: ScannerBackend? = null

    override fun start(onResult: (ScanResult) -> Unit) {
        stop()
        val backend = selectBackend(backends) ?: return
        activeBackend = backend
        backend.start { result ->
            onResult(result.copy(sourceType = name))
        }
    }

    override fun stop() {
        activeBackend?.stop()
        activeBackend = null
    }
}
