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

protocol CameraScanSession {
    func start(onDecoded: @escaping (_ symbology: String, _ rawValue: String) -> Void)
    func stop()
}

protocol ExternalScannerSession {
    func start(onPayload: @escaping ([String: String]) -> Void)
    func stop()
}

protocol ScannerBackend {
    var backendName: String { get }
    func isAvailable() -> Bool
    func start(onResult: @escaping (ScanResult) -> Void)
    func stop()
}

private func selectBackend(_ backends: [ScannerBackend]) -> ScannerBackend? {
    backends.first(where: { $0.isAvailable() }) ?? backends.first
}

final class NoOpBackend: ScannerBackend {
    let backendName: String
    private let defaultSource: String

    init(backendName: String, defaultSource: String) {
        self.backendName = backendName
        self.defaultSource = defaultSource
    }

    func isAvailable() -> Bool { true }

    func start(onResult: @escaping (ScanResult) -> Void) {
        onResult(
            ScanResult(
                symbology: "demo",
                rawValue: "\(backendName)_\(UUID().uuidString)",
                sourceType: defaultSource
            )
        )
    }

    func stop() {}
}

final class AVFoundationCameraBackend: ScannerBackend {
    let backendName: String = "avfoundation"
    private let session: CameraScanSession?

    init(session: CameraScanSession? = nil) {
        self.session = session
    }

    func isAvailable() -> Bool {
        session != nil
    }

    func start(onResult: @escaping (ScanResult) -> Void) {
        guard let session else { return }
        session.start { symbology, rawValue in
            onResult(
                ScanResult(
                    symbology: symbology.isEmpty ? "unknown" : symbology,
                    rawValue: rawValue,
                    sourceType: "camera"
                )
            )
        }
    }

    func stop() {
        session?.stop()
    }
}

final class ExternalScannerBackend: ScannerBackend {
    let backendName: String = "external_scanner"
    private let session: ExternalScannerSession?

    init(session: ExternalScannerSession? = nil) {
        self.session = session
    }

    func isAvailable() -> Bool {
        session != nil
    }

    func start(onResult: @escaping (ScanResult) -> Void) {
        guard let session else { return }
        session.start { payload in
            guard let result = parseExternalScannerPayload(payload) else { return }
            onResult(result)
        }
    }

    func stop() {
        session?.stop()
    }
}

func parseExternalScannerPayload(_ payload: [String: String]) -> ScanResult? {
    let rawValue = payload["data"] ?? payload["raw_value"]
    guard let rawValue, !rawValue.isEmpty else { return nil }

    let symbology = payload["symbology"] ?? payload["label_type"] ?? "unknown"
    return ScanResult(symbology: symbology, rawValue: rawValue, sourceType: "enterprise_scanner")
}

final class CameraScanProvider: ScanProvider {
    let name = "camera"
    private let backends: [ScannerBackend]
    private var activeBackend: ScannerBackend?

    init(backends: [ScannerBackend] = [
        AVFoundationCameraBackend(),
        NoOpBackend(backendName: "camera_fallback", defaultSource: "camera")
    ]) {
        self.backends = backends
    }

    func start(onResult: @escaping (ScanResult) -> Void) {
        stop()
        guard let backend = selectBackend(backends) else { return }
        activeBackend = backend
        backend.start { result in
            onResult(ScanResult(symbology: result.symbology, rawValue: result.rawValue, sourceType: self.name))
        }
    }

    func stop() {
        activeBackend?.stop()
        activeBackend = nil
    }
}

final class RfidScanProvider: ScanProvider {
    let name = "rfid"
    private let backends: [ScannerBackend]
    private var activeBackend: ScannerBackend?

    init(backends: [ScannerBackend] = [NoOpBackend(backendName: "rfid_stub", defaultSource: "rfid")]) {
        self.backends = backends
    }

    func start(onResult: @escaping (ScanResult) -> Void) {
        stop()
        guard let backend = selectBackend(backends) else { return }
        activeBackend = backend
        backend.start { result in
            onResult(ScanResult(symbology: result.symbology, rawValue: result.rawValue, sourceType: self.name))
        }
    }

    func stop() {
        activeBackend?.stop()
        activeBackend = nil
    }
}

final class EnterpriseScannerProvider: ScanProvider {
    let name = "enterprise_scanner"
    private let backends: [ScannerBackend]
    private var activeBackend: ScannerBackend?

    init(backends: [ScannerBackend] = [
        ExternalScannerBackend(),
        NoOpBackend(backendName: "external_scanner_stub", defaultSource: "enterprise_scanner")
    ]) {
        self.backends = backends
    }

    func start(onResult: @escaping (ScanResult) -> Void) {
        stop()
        guard let backend = selectBackend(backends) else { return }
        activeBackend = backend
        backend.start { result in
            onResult(ScanResult(symbology: result.symbology, rawValue: result.rawValue, sourceType: self.name))
        }
    }

    func stop() {
        activeBackend?.stop()
        activeBackend = nil
    }
}
