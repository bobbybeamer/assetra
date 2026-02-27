package com.assetra.sample

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.assetra.scan.CameraScanProvider
import com.assetra.scan.CameraXBarcodeSession
import com.assetra.scan.DataWedgeBroadcastSession
import com.assetra.scan.DataWedgeEnterpriseBackend
import com.assetra.scan.EnterpriseScannerProvider
import com.assetra.scan.MlKitCameraBackend
import com.assetra.scan.RfidScanProvider
import com.assetra.scan.ScanProvider
import com.assetra.scan.ZebraRfidBackend
import com.assetra.scan.ZebraRfidSession
import com.assetra.sync.SampleStoreHolder
import com.assetra.sync.sampleCapture

class ProductionScanComposeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                ProductionScanScreen(activity = this)
            }
        }
    }
}

@Composable
fun ProductionScanScreen(activity: ComponentActivity) {
    val scrollState = rememberScrollState()
    val scannerStatus = remember { mutableStateOf("Scanner: inactive") }
    val providerStatus = remember { mutableStateOf("Provider: none") }
    val lastScanStatus = remember { mutableStateOf("Last scan: none") }
    val status = remember { mutableStateOf("Idle") }
    val isCameraActive = remember { mutableStateOf(false) }

    val previewView = remember { PreviewView(activity) }
    val cameraSession = remember {
        CameraXBarcodeSession(
            activity = activity,
            previewView = previewView,
            debounceMs = 1200,
            onPermissionDenied = {
                activity.runOnUiThread {
                    Toast.makeText(activity, "Camera permission denied", Toast.LENGTH_LONG).show()
                }
            }
        )
    }

    val cameraProvider = remember {
        CameraScanProvider(
            backends = listOf(MlKitCameraBackend(session = cameraSession))
        )
    }

    val enterpriseProvider = remember {
        EnterpriseScannerProvider(
            backends = listOf(
                DataWedgeEnterpriseBackend(
                    session = DataWedgeBroadcastSession(activity, action = "com.symbol.datawedge.api.RESULT_ACTION")
                )
            )
        )
    }

    val rfidProvider = remember {
        RfidScanProvider(
            backends = listOf(ZebraRfidBackend(session = ZebraRfidSession(activity)))
        )
    }

    val activeProvider = remember { mutableStateOf<ScanProvider?>(null) }

    fun startProvider(provider: ScanProvider, providerName: String, scannerName: String, showCamera: Boolean) {
        activeProvider.value?.stop()
        activeProvider.value = provider
        isCameraActive.value = showCamera
        scannerStatus.value = "Scanner: $scannerName active"
        providerStatus.value = "Provider: $providerName"

        provider.start { result ->
            sampleCapture(SampleStoreHolder.store, result.rawValue)
            activity.runOnUiThread {
                lastScanStatus.value = "Last scan: ${result.rawValue}"
                status.value = "Captured: ${result.rawValue}"
            }
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            activeProvider.value?.stop()
            activeProvider.value = null
        }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Assetra Scan") }) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (isCameraActive.value) {
                AndroidView(
                    factory = { previewView },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(280.dp)
                )
            }

            Button(
                onClick = { startProvider(cameraProvider, "camera", "camera", true) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start Camera")
            }

            Button(
                onClick = { startProvider(enterpriseProvider, "enterprise", "enterprise", false) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start Enterprise Scanner")
            }

            Button(
                onClick = { startProvider(rfidProvider, "rfid", "rfid", false) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start RFID")
            }

            FilledTonalButton(
                onClick = {
                    activeProvider.value?.stop()
                    activeProvider.value = null
                    isCameraActive.value = false
                    scannerStatus.value = "Scanner: inactive"
                    providerStatus.value = "Provider: none"
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Stop Scanner")
            }

            ProductionStatusLine(label = "Scanner", value = scannerStatus.value)
            ProductionStatusLine(label = "Provider", value = providerStatus.value)
            ProductionStatusLine(label = "Last Scan", value = lastScanStatus.value)
            ProductionStatusLine(label = "Status", value = status.value)
        }
    }
}

@Composable
private fun ProductionStatusLine(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            fontSize = 12.sp,
            color = Color.Gray
        )
        Text(
            text = value,
            fontSize = 12.sp,
            color = Color.DarkGray
        )
    }
}
