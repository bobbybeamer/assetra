package com.assetra.scan

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class CameraXBarcodeSession(
    private val activity: ComponentActivity,
    private val previewView: PreviewView,
    private val debounceMs: Long = 1000,
    private val onPermissionDenied: (() -> Unit)? = null,
) : CameraScanSession {
    private var callback: ((String, String) -> Unit)? = null
    private var cameraExecutor: ExecutorService? = null
    private var cameraProvider: ProcessCameraProvider? = null
    private var started = false
    private var lastScanRawValue: String? = null
    private var lastScanAtMs: Long = 0

    private val permissionLauncher =
        activity.registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                startCamera()
            } else {
                onPermissionDenied?.invoke()
            }
        }

    private val scanner = BarcodeScanning.getClient(
        BarcodeScannerOptions.Builder()
            .setBarcodeFormats(
                com.google.mlkit.vision.barcode.Barcode.FORMAT_QR_CODE,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_CODE_128,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_CODE_39,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_EAN_8,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_EAN_13,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_UPC_A,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_UPC_E,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_PDF417,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_AZTEC,
                com.google.mlkit.vision.barcode.Barcode.FORMAT_DATA_MATRIX
            )
            .build()
    )

    override fun start(onDecoded: (symbology: String, rawValue: String) -> Unit) {
        callback = onDecoded
        started = true

        if (hasCameraPermission()) {
            startCamera()
        } else {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    override fun stop() {
        started = false
        callback = null
        cameraProvider?.unbindAll()
        cameraExecutor?.shutdown()
        cameraExecutor = null
    }

    private fun hasCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(activity, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
    }

    private fun startCamera() {
        if (!started) {
            return
        }

        val providerFuture = ProcessCameraProvider.getInstance(activity)
        providerFuture.addListener(
            {
                val provider = providerFuture.get()
                cameraProvider = provider
                provider.unbindAll()

                val preview = Preview.Builder().build().also {
                    it.surfaceProvider = previewView.surfaceProvider
                }

                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()

                val executor = cameraExecutor ?: Executors.newSingleThreadExecutor().also { cameraExecutor = it }

                analysis.setAnalyzer(executor) { imageProxy ->
                    val mediaImage = imageProxy.image
                    if (mediaImage == null) {
                        imageProxy.close()
                        return@setAnalyzer
                    }

                    val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
                    scanner.process(image)
                        .addOnSuccessListener { barcodes ->
                            val first = barcodes.firstOrNull { !it.rawValue.isNullOrBlank() }
                            if (first != null) {
                                val rawValue = first.rawValue.orEmpty()
                                val symbology = mapBarcodeFormat(first.format)
                                if (shouldEmit(rawValue)) {
                                    callback?.invoke(symbology, rawValue)
                                }
                            }
                        }
                        .addOnCompleteListener {
                            imageProxy.close()
                        }
                }

                provider.bindToLifecycle(
                    activity,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    analysis,
                )
            },
            ContextCompat.getMainExecutor(activity),
        )
    }

    private fun shouldEmit(rawValue: String): Boolean {
        val now = System.currentTimeMillis()
        val isDuplicate = rawValue == lastScanRawValue && (now - lastScanAtMs) < debounceMs
        if (isDuplicate) {
            return false
        }
        lastScanRawValue = rawValue
        lastScanAtMs = now
        return true
    }

    private fun mapBarcodeFormat(format: Int): String {
        return when (format) {
            com.google.mlkit.vision.barcode.Barcode.FORMAT_QR_CODE -> "qr_code"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_CODE_128 -> "code_128"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_CODE_39 -> "code_39"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_EAN_8 -> "ean_8"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_EAN_13 -> "ean_13"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_UPC_A -> "upc_a"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_UPC_E -> "upc_e"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_PDF417 -> "pdf417"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_AZTEC -> "aztec"
            com.google.mlkit.vision.barcode.Barcode.FORMAT_DATA_MATRIX -> "data_matrix"
            else -> "unknown"
        }
    }
}