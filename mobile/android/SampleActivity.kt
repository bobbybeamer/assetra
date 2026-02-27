package com.assetra.sample

import android.os.Bundle
import android.graphics.Color
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import android.content.Intent
import androidx.activity.ComponentActivity
import androidx.camera.view.PreviewView

import com.assetra.conflicts.ConflictResolutionActivity
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

class SampleActivity : ComponentActivity() {
    private val dataWedgeAction = "com.symbol.datawedge.api.RESULT_ACTION"
    private lateinit var cameraProvider: ScanProvider
    private lateinit var enterpriseProvider: ScanProvider
    private lateinit var rfidProvider: ScanProvider
    private var activeProvider: ScanProvider? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val previewView = PreviewView(this)
        val cameraSession = CameraXBarcodeSession(
            activity = this,
            previewView = previewView,
            debounceMs = 1200,
            onPermissionDenied = {
                runOnUiThread {
                    Toast.makeText(this, "Camera permission denied", Toast.LENGTH_LONG).show()
                }
            }
        )

        cameraProvider = CameraScanProvider(
            backends = listOf(
                MlKitCameraBackend(session = cameraSession)
            )
        )
        enterpriseProvider = EnterpriseScannerProvider(
            backends = listOf(
                DataWedgeEnterpriseBackend(session = DataWedgeBroadcastSession(this, action = dataWedgeAction))
            )
        )
        rfidProvider = RfidScanProvider(
            backends = listOf(
                ZebraRfidBackend(session = ZebraRfidSession(this))
            )
        )

        val baseUrlInput = EditText(this).apply { hint = "Base URL" }
        val tenantInput = EditText(this).apply { hint = "Tenant ID" }
        val usernameInput = EditText(this).apply { hint = "Username" }
        val passwordInput = EditText(this).apply { hint = "Password" }
        val startCameraButton = Button(this).apply { text = "Start Camera Provider" }
        val startEnterpriseButton = Button(this).apply { text = "Start Enterprise Provider" }
        val startRfidButton = Button(this).apply { text = "Start RFID Provider" }
        val stopScannerButton = Button(this).apply { text = "Stop Active Scanner" }
        val scannerStatus = TextView(this).apply {
            text = "Scanner: inactive"
            setTextColor(Color.GRAY)
        }
        val providerStatus = TextView(this).apply { text = "Provider: none" }
        val lastScanStatus = TextView(this).apply { text = "Last scan: none" }
        val dataWedgeStatus = TextView(this).apply { text = "DataWedge action: $dataWedgeAction" }
        val runButton = Button(this).apply { text = "Sync Pending Events" }
        val conflictsButton = Button(this).apply { text = "View Conflicts" }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(baseUrlInput)
            addView(tenantInput)
            addView(usernameInput)
            addView(passwordInput)
            addView(previewView)
            addView(startCameraButton)
            addView(startEnterpriseButton)
            addView(startRfidButton)
            addView(stopScannerButton)
            addView(scannerStatus)
            addView(providerStatus)
            addView(lastScanStatus)
            addView(dataWedgeStatus)
            addView(runButton)
            addView(conflictsButton)
        }
        setContentView(layout)

        val handleScan: (String) -> Unit = { rawValue ->
            sampleCapture(SampleStoreHolder.store, rawValue)
            runOnUiThread {
                lastScanStatus.text = "Last scan: $rawValue"
                Toast.makeText(this, "Captured: $rawValue", Toast.LENGTH_SHORT).show()
            }
        }

        startCameraButton.setOnClickListener {
            activeProvider?.stop()
            activeProvider = cameraProvider
            cameraProvider.start { result -> handleScan(result.rawValue) }
            scannerStatus.text = "Scanner: camera active"
            scannerStatus.setTextColor(Color.parseColor("#2E7D32"))
            providerStatus.text = "Provider: camera"
            Toast.makeText(this, "Camera provider started", Toast.LENGTH_SHORT).show()
        }

        startEnterpriseButton.setOnClickListener {
            activeProvider?.stop()
            activeProvider = enterpriseProvider
            enterpriseProvider.start { result -> handleScan(result.rawValue) }
            scannerStatus.text = "Scanner: enterprise active"
            scannerStatus.setTextColor(Color.parseColor("#2E7D32"))
            providerStatus.text = "Provider: enterprise"
            Toast.makeText(this, "Enterprise provider started", Toast.LENGTH_SHORT).show()
        }

        startRfidButton.setOnClickListener {
            activeProvider?.stop()
            activeProvider = rfidProvider
            rfidProvider.start { result -> handleScan(result.rawValue) }
            scannerStatus.text = "Scanner: rfid active"
            scannerStatus.setTextColor(Color.parseColor("#2E7D32"))
            providerStatus.text = "Provider: rfid"
            Toast.makeText(this, "RFID provider started", Toast.LENGTH_SHORT).show()
        }

        stopScannerButton.setOnClickListener {
            activeProvider?.stop()
            activeProvider = null
            scannerStatus.text = "Scanner: inactive"
            scannerStatus.setTextColor(Color.GRAY)
            providerStatus.text = "Provider: none"
            Toast.makeText(this, "Scanner stopped", Toast.LENGTH_SHORT).show()
        }

        runButton.setOnClickListener {
            val baseUrl = baseUrlInput.text.toString()
            val tenantId = tenantInput.text.toString()
            val username = usernameInput.text.toString()
            val password = passwordInput.text.toString()

            if (baseUrl.isBlank() || tenantId.isBlank() || username.isBlank() || password.isBlank()) {
                Toast.makeText(this, "Fill all fields", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            try {
                SampleAppRunner.runSyncOnly(
                    baseUrl = baseUrl,
                    tenantId = tenantId,
                    username = username,
                    password = password,
                )
                Toast.makeText(this, "Sync completed", Toast.LENGTH_SHORT).show()
            } catch (ex: Exception) {
                Toast.makeText(this, "Sync failed: ${ex.message}", Toast.LENGTH_LONG).show()
            }
        }

        conflictsButton.setOnClickListener {
            startActivity(Intent(this, ConflictResolutionActivity::class.java))
        }
    }

    override fun onStop() {
        activeProvider?.stop()
        activeProvider = null
        super.onStop()
    }
}
