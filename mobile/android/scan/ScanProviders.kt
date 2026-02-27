package com.assetra.scan

import android.content.Context
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit
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

interface RfidScanSession {
    fun isAvailable(): Boolean
    fun start(onTagRead: (epc: String, details: Map<String, String>) -> Unit)
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

class ZebraRfidSession(
    private val context: Context,
    private val pollIntervalMs: Long = 700,
) : RfidScanSession {
    private var readers: Any? = null
    private var reader: Any? = null
    private var callback: ((String, Map<String, String>) -> Unit)? = null
    private var poller: ScheduledExecutorService? = null
    private var running = false

    override fun isAvailable(): Boolean {
        return try {
            Class.forName("com.zebra.rfid.api3.Readers")
            true
        } catch (_: ClassNotFoundException) {
            false
        }
    }

    override fun start(onTagRead: (epc: String, details: Map<String, String>) -> Unit) {
        stop()
        callback = onTagRead
        if (!isAvailable()) {
            return
        }

        try {
            val readersClass = Class.forName("com.zebra.rfid.api3.Readers")
            val enumTransportClass = Class.forName("com.zebra.rfid.api3.ENUM_TRANSPORT")
            @Suppress("UNCHECKED_CAST")
            val enumType = enumTransportClass as Class<out Enum<*>>
            val bluetooth = java.lang.Enum.valueOf(enumType, "BLUETOOTH")

            val ctor = readersClass.getConstructor(Context::class.java, enumTransportClass)
            readers = ctor.newInstance(context, bluetooth)

            @Suppress("UNCHECKED_CAST")
            val devices = readersClass
                .getMethod("GetAvailableRFIDReaderList")
                .invoke(readers) as? List<Any?>

            val firstDevice = devices?.firstOrNull() ?: return
            val readerDeviceClass = Class.forName("com.zebra.rfid.api3.ReaderDevice")
            val currentReader = readerDeviceClass.getMethod("getRFIDReader").invoke(firstDevice)
            reader = currentReader

            val readerClass = Class.forName("com.zebra.rfid.api3.RFIDReader")
            readerClass.getMethod("connect").invoke(currentReader)

            val actions = resolveReaderActions(currentReader)
            val actionsClass = actions.javaClass
            val inventory = resolveInventoryActions(actions)
            inventory.javaClass.getMethod("perform").invoke(inventory)

            running = true
            poller = Executors.newSingleThreadScheduledExecutor().also { executor ->
                executor.scheduleAtFixedRate(
                    { readTagsBatch() },
                    pollIntervalMs,
                    pollIntervalMs,
                    TimeUnit.MILLISECONDS,
                )
            }
        } catch (_: Exception) {
            stop()
        }
    }

    override fun stop() {
        running = false
        poller?.shutdownNow()
        poller = null

        try {
            val currentReader = reader
            if (currentReader != null) {
                val readerClass = Class.forName("com.zebra.rfid.api3.RFIDReader")
                val actions = resolveReaderActions(currentReader)
                val inventory = resolveInventoryActions(actions)
                inventory.javaClass.getMethod("stop").invoke(inventory)
                readerClass.getMethod("disconnect").invoke(currentReader)
            }
        } catch (_: Exception) {
        }

        try {
            readers?.javaClass?.getMethod("Dispose")?.invoke(readers)
        } catch (_: Exception) {
        }

        reader = null
        readers = null
        callback = null
    }

    private fun readTagsBatch() {
        if (!running) {
            return
        }

        try {
            val currentReader = reader ?: return
            val readerClass = Class.forName("com.zebra.rfid.api3.RFIDReader")
            val actions = resolveReaderActions(currentReader)
            val tagsAny = actions.javaClass.getMethod("getReadTags", Int::class.javaPrimitiveType).invoke(actions, 100)
            val tags = when (tagsAny) {
                is Array<*> -> tagsAny.toList()
                else -> emptyList<Any?>()
            }

            tags.forEach { tag ->
                if (tag == null) return@forEach
                val tagClass = tag.javaClass
                val epc = runCatching { tagClass.getMethod("getTagID").invoke(tag) as? String }
                    .getOrNull()
                    ?.trim()
                    .orEmpty()
                if (epc.isBlank()) {
                    return@forEach
                }
                val peakRssi = runCatching { tagClass.getMethod("getPeakRSSI").invoke(tag)?.toString().orEmpty() }
                    .getOrDefault("")
                callback?.invoke(
                    epc,
                    mapOf(
                        "peak_rssi" to peakRssi,
                        "transport" to "bluetooth",
                    )
                )
            }
        } catch (_: Exception) {
        }
    }

    private fun resolveReaderActions(currentReader: Any): Any {
        return runCatching {
            currentReader.javaClass.getMethod("getActions").invoke(currentReader)
        }.getOrElse {
            currentReader.javaClass.getField("Actions").get(currentReader)
        }
    }

    private fun resolveInventoryActions(actions: Any): Any {
        return runCatching {
            actions.javaClass.getMethod("getInventory").invoke(actions)
        }.getOrElse {
            actions.javaClass.getField("Inventory").get(actions)
        }
    }
}

class ZebraRfidBackend(
    private val session: RfidScanSession? = null,
) : ScannerBackend {
    override val backendName: String = "zebra_rfid_api3"

    override fun isAvailable(): Boolean {
        return session?.isAvailable() == true
    }

    override fun start(onResult: (ScanResult) -> Unit) {
        val activeSession = session ?: return
        activeSession.start { epc, details ->
            val rssi = details["peak_rssi"]
            val rawValue = if (!rssi.isNullOrBlank()) {
                "$epc;rssi=$rssi"
            } else {
                epc
            }
            onResult(
                ScanResult(
                    symbology = "epc",
                    rawValue = rawValue,
                    sourceType = "rfid",
                )
            )
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
        ZebraRfidBackend(),
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
