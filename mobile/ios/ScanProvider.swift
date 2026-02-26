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

final class CameraScanProvider: ScanProvider {
    let name = "camera"
    private let backends: [ScannerBackend]
    private var activeBackend: ScannerBackend?

    init(backends: [ScannerBackend] = [NoOpBackend(backendName: "avfoundation", defaultSource: "camera")]) {
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

    init(backends: [ScannerBackend] = [NoOpBackend(backendName: "external_scanner_stub", defaultSource: "enterprise_scanner")]) {
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
