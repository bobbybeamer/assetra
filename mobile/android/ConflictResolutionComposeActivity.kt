package com.assetra.conflicts

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.assetra.sync.ConflictRecord
import com.assetra.sync.SampleStoreHolder
import kotlinx.coroutines.launch

class ConflictResolutionComposeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme {
                ConflictResolutionScreen()
            }
        }
    }
}

@Composable
fun ConflictResolutionScreen() {
    val localStore = SampleStoreHolder.store
    val conflicts = remember { mutableStateOf(emptyList<ConflictRecord>()) }
    val coroutineScope = rememberCoroutineScope()

    // Load conflicts on first compose
    remember {
        coroutineScope.launch {
            val pending = localStore.pendingConflicts()
            if (pending.isEmpty()) {
                localStore.seedConflicts(
                    listOf(
                        ConflictRecord(
                            id = "A-1001:status",
                            assetId = "A-1001",
                            field = "status",
                            localValue = "in_transit",
                            serverValue = "in_warehouse",
                            updatedAt = "2026-02-25T19:10:00Z",
                        )
                    )
                )
                conflicts.value = listOf(
                    ConflictRecord(
                        id = "A-1001:status",
                        assetId = "A-1001",
                        field = "status",
                        localValue = "in_transit",
                        serverValue = "in_warehouse",
                        updatedAt = "2026-02-25T19:10:00Z",
                    )
                )
            } else {
                conflicts.value = pending
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Conflict Resolution") }
            )
        }
    ) { paddingValues ->
        if (conflicts.value.isEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text("No conflicts", fontSize = 18.sp)
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(conflicts.value) { conflict ->
                    ConflictCard(
                        conflict = conflict,
                        onAcceptServer = {
                            coroutineScope.launch {
                                localStore.resolveConflict(conflict.id, useServerValue = true)
                                conflicts.value = conflicts.value.filter { it.id != conflict.id }
                            }
                        },
                        onKeepLocal = {
                            coroutineScope.launch {
                                localStore.resolveConflict(conflict.id, useServerValue = false)
                                conflicts.value = conflicts.value.filter { it.id != conflict.id }
                            }
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun ConflictCard(
    conflict: ConflictRecord,
    onAcceptServer: () -> Unit,
    onKeepLocal: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Asset ${conflict.assetId} (${conflict.field})",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text("Local: ${conflict.localValue}", fontSize = 13.sp)
                Text("Server: ${conflict.serverValue}", fontSize = 13.sp)
                Text(
                    "Updated: ${conflict.updatedAt}",
                    fontSize = 11.sp,
                    color = androidx.compose.ui.graphics.Color.Gray
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onAcceptServer,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Accept Server")
                }
                FilledTonalButton(
                    onClick = onKeepLocal,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Keep Local")
                }
            }
        }
    }
}
