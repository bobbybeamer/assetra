package com.assetra.sample

import android.content.Intent
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.assetra.conflicts.ConflictResolutionComposeActivity
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
import com.assetra.sync.SampleAppRunner
import com.assetra.sync.SampleStoreHolder
import com.assetra.sync.sampleCapture
import kotlinx.coroutines.launch

class SampleComposeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme {
                SampleSyncScreen(activity = this)
            }
        }
    }
}

@Composable
fun SampleSyncScreen(activity: ComponentActivity) {
    val scrollState = rememberScrollState()
    val coroutineScope = rememberCoroutineScope()

    val baseUrl = remember { mutableStateOf("https://api.assetra.example") }
    val tenantId = remember { mutableStateOf("1") }
    val username = remember { mutableStateOf("") }
    val password = remember { mutableStateOf("") }
    val status = remember { mutableStateOf("Idle") }
    val scannerStatus = remember { mutableStateOf("Scanner: inactive") }
    val providerStatus = remember { mutableStateOf("Provider: none") }
    val lastScanStatus = remember { mutableStateOf("Last scan: none") }
    val isScanning = remember { mutableStateOf(false) }

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
            backends = listOf(
                MlKitCameraBackend(session = cameraSession)
            )
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
            backends = listOf(
                ZebraRfidBackend(session = ZebraRfidSession(activity))
            )
        )
    }

        val activeProvider = remember { mutableStateOf<ScanProvider?>(null) }

    val handleScan: (String) -> Unit = { rawValue ->
        sampleCapture(SampleStoreHolder.store, rawValue)
        activity.runOnUiThread {
            lastScanStatus.value = "Last scan: $rawValue"
            Toast.makeText(activity, "Captured: $rawValue", Toast.LENGTH_SHORT).show()
        }
    }

    DisposableEffect(Unit) {
        onDispose {
                    activeProvider.value?.stop()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Assetra Sample") }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // API Configuration
            OutlinedTextField(
                value = baseUrl.value,
                onValueChange = { baseUrl.value = it },
                label = { Text("Base URL") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            OutlinedTextField(
                value = tenantId.value,
                onValueChange = { tenantId.value = it },
                label = { Text("Tenant ID") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
            )

            OutlinedTextField(
                value = username.value,
                onValueChange = { username.value = it },
                label = { Text("Username") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            OutlinedTextField(
                value = password.value,
                onValueChange = { password.value = it },
                label = { Text("Password") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                visualTransformation = PasswordVisualTransformation()
            )

            // Camera Preview
            if (isScanning.value) {
                AndroidView(
                    factory = { previewView },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(300.dp)
                )
            }

            // Scanner Controls
            Button(
                onClick = {
                        activeProvider.value?.stop()
                        activeProvider.value = cameraProvider
                    isScanning.value = true
                    cameraProvider.start { result -> handleScan(result.rawValue) }
                    scannerStatus.value = "Scanner: camera active"
                    providerStatus.value = "Provider: camera"
                    Toast.makeText(activity, "Camera provider started", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start Camera Provider")
            }

            Button(
                onClick = {
                        activeProvider.value?.stop()
                        activeProvider.value = enterpriseProvider
                    isScanning.value = false
                    enterpriseProvider.start { result -> handleScan(result.rawValue) }
                    scannerStatus.value = "Scanner: enterprise active"
                    providerStatus.value = "Provider: enterprise"
                    Toast.makeText(activity, "Enterprise provider started", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start Enterprise Provider")
            }

            Button(
                onClick = {
                        activeProvider.value?.stop()
                        activeProvider.value = rfidProvider
                    isScanning.value = false
                    rfidProvider.start { result -> handleScan(result.rawValue) }
                    scannerStatus.value = "Scanner: rfid active"
                    providerStatus.value = "Provider: rfid"
                    Toast.makeText(activity, "RFID provider started", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Start RFID Provider")
            }

            Button(
                onClick = {
                    // Simulate enterprise scan
                    activity.sendBroadcast(
                        android.content.Intent().apply {
                            action = "com.symbol.datawedge.api.RESULT_ACTION"
                            putExtra(
                                "com.symbol.datawedge.data_string",
                                "ENT-${java.util.UUID.randomUUID().toString().take(8)}"
                            )
                            putExtra("com.symbol.datawedge.label_type", "code128")
                        }
                    )
                    Toast.makeText(activity, "Simulated enterprise scan", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Simulate Enterprise Scan")
            }

            FilledTonalButton(
                onClick = {
                        activeProvider.value?.stop()
                        activeProvider.value = null
                    isScanning.value = false
                    scannerStatus.value = "Scanner: inactive"
                    providerStatus.value = "Provider: none"
                    Toast.makeText(activity, "Scanner stopped", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Stop Active Scanner")
            }

            // Status Display
            StatusLine(label = "Scanner", value = scannerStatus.value)
            StatusLine(label = "Provider", value = providerStatus.value)
            StatusLine(label = "Last Scan", value = lastScanStatus.value)
            StatusLine(label = "Status", value = status.value)

            // Sync Controls
            Button(
                onClick = {
                    if (baseUrl.value.isBlank() || tenantId.value.isBlank() ||
                        username.value.isBlank() || password.value.isBlank()
                    ) {
                        Toast.makeText(activity, "Fill all fields", Toast.LENGTH_SHORT).show()
                        return@Button
                    }

                    coroutineScope.launch {
                        status.value = "Running..."
                        try {
                            SampleAppRunner.runSyncOnly(
                                baseUrl = baseUrl.value,
                                tenantId = tenantId.value,
                                username = username.value,
                                password = password.value
                            )
                            status.value = "Sync completed"
                            Toast.makeText(activity, "Sync completed", Toast.LENGTH_SHORT).show()
                        } catch (ex: Exception) {
                            status.value = "Sync failed: ${ex.localizedMessage}"
                            Toast.makeText(activity, "Sync failed: ${ex.message}", Toast.LENGTH_LONG).show()
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Sync Pending Events")
            }

            Button(
                onClick = {
                    activity.startActivity(Intent(activity, ConflictResolutionComposeActivity::class.java))
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("View Conflicts")
            }
        }
    }
}

@Composable
fun StatusLine(label: String, value: String) {
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
