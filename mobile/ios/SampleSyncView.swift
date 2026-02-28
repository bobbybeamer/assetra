import SwiftUI

final class SampleScannerController: ObservableObject {
    @Published var scannerStatus = "Scanner: inactive"
    @Published var providerStatus = "Provider: none"
    @Published var lastScanStatus = "Last scan: none"

    private let cameraProvider: ScanProvider
    private let enterpriseProvider: ScanProvider
    private let rfidProvider: ScanProvider
    private var activeProvider: ScanProvider?

    init() {
        let cameraSession = AVFoundationCameraSession(
            debounceMs: 1200,
            onPermissionDenied: {}
        )
        self.cameraProvider = CameraScanProvider(
            backends: [AVFoundationCameraBackend(session: cameraSession)]
        )

        let externalSession = NotificationExternalScannerSession()
        self.enterpriseProvider = EnterpriseScannerProvider(
            backends: [ExternalScannerBackend(session: externalSession)]
        )

        let rfidSession = makeDefaultRfidSession()
        self.rfidProvider = RfidScanProvider(
            backends: [ZebraRfidBackend(session: rfidSession)]
        )
    }

    func startCamera(onCapture: @escaping (String) -> Void) {
        stopActive()
        activeProvider = cameraProvider
        providerStatus = "Provider: camera"
        scannerStatus = "Scanner: camera active"

        cameraProvider.start { [weak self] result in
            DispatchQueue.main.async {
                self?.lastScanStatus = "Last scan: \(result.rawValue)"
            }
            onCapture(result.rawValue)
        }
    }

    func startEnterprise(onCapture: @escaping (String) -> Void) {
        stopActive()
        activeProvider = enterpriseProvider
        providerStatus = "Provider: enterprise"
        scannerStatus = "Scanner: enterprise active"

        enterpriseProvider.start { [weak self] result in
            DispatchQueue.main.async {
                self?.lastScanStatus = "Last scan: \(result.rawValue)"
            }
            onCapture(result.rawValue)
        }
    }

    func startRfid(onCapture: @escaping (String) -> Void) {
        stopActive()
        activeProvider = rfidProvider
        providerStatus = "Provider: rfid"
        scannerStatus = "Scanner: rfid active"

        rfidProvider.start { [weak self] result in
            DispatchQueue.main.async {
                self?.lastScanStatus = "Last scan: \(result.rawValue)"
            }
            onCapture(result.rawValue)
        }
    }

    func stopActive() {
        activeProvider?.stop()
        activeProvider = nil
        providerStatus = "Provider: none"
        scannerStatus = "Scanner: inactive"
    }
}

struct SampleSyncView: View {
    @StateObject private var scanner = SampleScannerController()
    @State private var baseUrl = "https://api.assetra.example"
    @State private var tenantId = "1"
    @State private var username = ""
    @State private var password = ""
    @State private var status = "Idle"
    @State private var showConflicts = false

    var body: some View {
        VStack(spacing: 12) {
            TextField("Base URL", text: $baseUrl)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .textFieldStyle(.roundedBorder)
            TextField("Tenant ID", text: $tenantId)
                .textFieldStyle(.roundedBorder)
            TextField("Username", text: $username)
                .textFieldStyle(.roundedBorder)
            SecureField("Password", text: $password)
                .textFieldStyle(.roundedBorder)

            Button("Start Camera Provider") {
                scanner.startCamera { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Start Enterprise Provider") {
                scanner.startEnterprise { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Start RFID Provider") {
                scanner.startRfid { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Simulate Enterprise Scan") {
                NotificationCenter.default.post(
                    name: NotificationExternalScannerSession.defaultNotificationName,
                    object: nil,
                    userInfo: [
                        "data": "ENT-\(UUID().uuidString.prefix(8))",
                        "symbology": "code128"
                    ]
                )
            }

            Button("Simulate RFID Scan") {
                NotificationCenter.default.post(
                    name: NotificationRfidSession.defaultNotificationName,
                    object: nil,
                    userInfo: [
                        "epc": "E200-\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(8))",
                        "peak_rssi": "-55"
                    ]
                )
            }

            Button("Stop Active Scanner") {
                scanner.stopActive()
            }

            Text(scanner.scannerStatus)
                .font(.footnote)
                .foregroundColor(.secondary)

            Text(scanner.providerStatus)
                .font(.footnote)
                .foregroundColor(.secondary)

            Text(scanner.lastScanStatus)
                .font(.footnote)
                .foregroundColor(.secondary)

            Button("Sync Pending Events") {
                Task {
                    status = "Running..."
                    do {
                        try await SampleAppRunner.runSyncOnly(
                            baseURL: URL(string: baseUrl)!,
                            tenantId: tenantId,
                            username: username,
                            password: password
                        )
                        status = "Sync completed"
                    } catch {
                        status = "Sync failed: \(error.localizedDescription)"
                    }
                }
            }

            Button("View Conflicts") {
                showConflicts = true
            }

            Text(status)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .sheet(isPresented: $showConflicts) {
            NavigationView {
                ConflictResolutionView(store: SampleStoreHolder.sharedStore)
            }
        }
        .onDisappear {
            scanner.stopActive()
        }
    }
}

#Preview {
    SampleSyncView()
}
