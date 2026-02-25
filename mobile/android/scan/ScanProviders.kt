package com.assetra.scan

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

class CameraScanProvider : ScanProvider {
    override val name: String = "camera"

    override fun start(onResult: (ScanResult) -> Unit) {
        // TODO: integrate camera SDK (ML Kit / ZXing)
    }

    override fun stop() {
        // TODO: stop camera stream
    }
}

class RfidScanProvider : ScanProvider {
    override val name: String = "rfid"

    override fun start(onResult: (ScanResult) -> Unit) {
        // TODO: integrate RFID SDK (e.g., nur_sdk)
    }

    override fun stop() {
        // TODO: stop RFID stream
    }
}

class EnterpriseScannerProvider : ScanProvider {
    override val name: String = "enterprise_scanner"

    override fun start(onResult: (ScanResult) -> Unit) {
        // TODO: integrate hardware scanner intent broadcast
    }

    override fun stop() {
        // TODO: stop scanner intent subscription
    }
}
