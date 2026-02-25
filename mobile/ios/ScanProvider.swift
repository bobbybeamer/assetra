import Foundation

protocol ScanProvider {
    var name: String { get }
    func start(onResult: @escaping (ScanResult) -> Void)
    func stop()
}

struct ScanResult {
    let symbology: String
    let rawValue: String
    let sourceType: String
}

final class CameraScanProvider: ScanProvider {
    let name = "camera"

    func start(onResult: @escaping (ScanResult) -> Void) {
        // TODO: integrate camera SDK (AVFoundation + Vision)
    }

    func stop() {
        // TODO: stop camera session
    }
}

final class RfidScanProvider: ScanProvider {
    let name = "rfid"

    func start(onResult: @escaping (ScanResult) -> Void) {
        // TODO: integrate RFID SDK
    }

    func stop() {
        // TODO: stop RFID stream
    }
}

final class EnterpriseScannerProvider: ScanProvider {
    let name = "enterprise_scanner"

    func start(onResult: @escaping (ScanResult) -> Void) {
        // TODO: integrate external scanner callbacks
    }

    func stop() {
        // TODO: stop external scanner callbacks
    }
}
