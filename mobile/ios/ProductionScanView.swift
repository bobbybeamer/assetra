import SwiftUI

struct ProductionScanView: View {
    @StateObject private var scanner = SampleScannerController()
    @State private var status = "Idle"

    var body: some View {
        VStack(spacing: 12) {
            Button("Start Camera") {
                scanner.startCamera { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Start Enterprise Scanner") {
                scanner.startEnterprise { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Start RFID") {
                scanner.startRfid { rawValue in
                    sampleCapture(localStore: SampleStoreHolder.sharedStore, rawValue: rawValue)
                    status = "Captured: \(rawValue)"
                }
            }

            Button("Stop Scanner") {
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

            Text(status)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding()
        .navigationTitle("Scan")
        .onDisappear {
            scanner.stopActive()
        }
    }
}

#Preview {
    NavigationView {
        ProductionScanView()
    }
}
