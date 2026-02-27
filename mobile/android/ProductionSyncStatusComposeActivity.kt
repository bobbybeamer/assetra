package com.assetra.sample

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.assetra.conflicts.ConflictResolutionComposeActivity
import com.assetra.sync.SampleStoreHolder
import kotlinx.coroutines.launch

class ProductionSyncStatusComposeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                ProductionSyncStatusScreen(activity = this)
            }
        }
    }
}

@Composable
fun ProductionSyncStatusScreen(activity: ComponentActivity) {
    val scrollState = rememberScrollState()
    val coroutineScope = rememberCoroutineScope()

    val baseUrl = remember { mutableStateOf("https://api.assetra.example") }
    val tenantId = remember { mutableStateOf("1") }
    val username = remember { mutableStateOf("") }
    val password = remember { mutableStateOf("") }

    val pendingCount = remember { mutableStateOf(0) }
    val conflictCount = remember { mutableStateOf(0) }
    val lastSyncAt = remember { mutableStateOf("Never") }
    val status = remember { mutableStateOf("Idle") }

    suspend fun refreshStatus() {
        pendingCount.value = SampleStoreHolder.store.pendingScanEvents().size
        conflictCount.value = SampleStoreHolder.store.pendingConflicts().size
        lastSyncAt.value = SampleStoreHolder.store.lastSyncAt() ?: "Never"
    }

    LaunchedEffect(Unit) {
        refreshStatus()
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Sync Status") }) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
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

            Button(
                onClick = {
                    coroutineScope.launch {
                        refreshStatus()
                        status.value = "Status refreshed"
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Refresh Status")
            }

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
                        refreshStatus()
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Retry Sync")
            }

            Button(
                onClick = {
                    activity.startActivity(Intent(activity, ConflictResolutionComposeActivity::class.java))
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = conflictCount.value > 0
            ) {
                Text("Resolve Conflicts")
            }

            Text("Pending queue: ${pendingCount.value}")
            Text("Pending conflicts: ${conflictCount.value}")
            Text("Last sync at: ${lastSyncAt.value}")
            Text(status.value)
        }
    }
}
