import AVFoundation
import Foundation
import QuartzCore

final class AVFoundationCameraSession: NSObject, CameraScanSession, AVCaptureMetadataOutputObjectsDelegate {
    private let captureSession = AVCaptureSession()
    private let metadataOutput = AVCaptureMetadataOutput()
    private let metadataQueue = DispatchQueue(label: "com.assetra.camera.metadata")

    private let previewContainerLayer: CALayer?
    private let onPermissionDenied: (() -> Void)?
    private let debounceMs: TimeInterval

    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var onDecoded: ((_ symbology: String, _ rawValue: String) -> Void)?
    private var started = false
    private var lastRawValue: String?
    private var lastDecodedAt: Date?

    init(
        previewContainerLayer: CALayer? = nil,
        debounceMs: TimeInterval = 1000,
        onPermissionDenied: (() -> Void)? = nil
    ) {
        self.previewContainerLayer = previewContainerLayer
        self.debounceMs = debounceMs
        self.onPermissionDenied = onPermissionDenied
        super.init()
    }

    func start(onDecoded: @escaping (_ symbology: String, _ rawValue: String) -> Void) {
        stop()
        self.onDecoded = onDecoded

        let status = AVCaptureDevice.authorizationStatus(for: .video)
        switch status {
        case .authorized:
            configureAndStartIfNeeded()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                guard let self else { return }
                if granted {
                    self.configureAndStartIfNeeded()
                } else {
                    self.onPermissionDenied?()
                }
            }
        default:
            onPermissionDenied?()
        }
    }

    func stop() {
        started = false
        onDecoded = nil
        lastRawValue = nil
        lastDecodedAt = nil

        if captureSession.isRunning {
            captureSession.stopRunning()
        }

        captureSession.inputs.forEach { captureSession.removeInput($0) }
        captureSession.outputs.forEach { captureSession.removeOutput($0) }

        previewLayer?.removeFromSuperlayer()
        previewLayer = nil
    }

    private func configureAndStartIfNeeded() {
        guard !started else { return }
        started = true

        do {
            let camera = AVCaptureDevice.default(for: .video)
            guard let camera else {
                started = false
                return
            }

            let input = try AVCaptureDeviceInput(device: camera)
            if captureSession.canAddInput(input) {
                captureSession.addInput(input)
            }

            if captureSession.canAddOutput(metadataOutput) {
                captureSession.addOutput(metadataOutput)
                metadataOutput.setMetadataObjectsDelegate(self, queue: metadataQueue)

                let supportedTypes = metadataOutput.availableMetadataObjectTypes
                let preferred: [AVMetadataObject.ObjectType] = [
                    .qr,
                    .ean8,
                    .ean13,
                    .code128,
                    .code39,
                    .upce,
                    .pdf417,
                    .dataMatrix,
                    .aztec
                ]
                metadataOutput.metadataObjectTypes = preferred.filter { supportedTypes.contains($0) }
            }

            if let previewContainerLayer {
                let preview = AVCaptureVideoPreviewLayer(session: captureSession)
                preview.videoGravity = .resizeAspectFill
                preview.frame = previewContainerLayer.bounds
                previewContainerLayer.addSublayer(preview)
                previewLayer = preview
            }

            captureSession.startRunning()
        } catch {
            started = false
        }
    }

    func metadataOutput(
        _ output: AVCaptureMetadataOutput,
        didOutput metadataObjects: [AVMetadataObject],
        from connection: AVCaptureConnection
    ) {
        guard let first = metadataObjects.compactMap({ $0 as? AVMetadataMachineReadableCodeObject }).first,
              let rawValue = first.stringValue,
              shouldEmit(rawValue: rawValue) else {
            return
        }

        let symbology = first.type.rawValue
        onDecoded?(symbology, rawValue)
    }

    private func shouldEmit(rawValue: String) -> Bool {
        let now = Date()
        if let lastRawValue,
           let lastDecodedAt,
           rawValue == lastRawValue,
           now.timeIntervalSince(lastDecodedAt) * 1000 < debounceMs {
            return false
        }

        self.lastRawValue = rawValue
        self.lastDecodedAt = now
        return true
    }
}
