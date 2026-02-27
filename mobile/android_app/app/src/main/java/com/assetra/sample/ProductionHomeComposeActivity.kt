package com.assetra.sample

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
class ProductionHomeComposeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Scaffold(topBar = { TopAppBar(title = { Text("Assetra") }) }) { paddingValues ->
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(paddingValues)
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Button(
                            onClick = {
                                startActivity(Intent(this@ProductionHomeComposeActivity, ProductionScanComposeActivity::class.java))
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Open Scan")
                        }

                        Button(
                            onClick = {
                                startActivity(Intent(this@ProductionHomeComposeActivity, ProductionSyncStatusComposeActivity::class.java))
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Open Sync Status")
                        }
                    }
                }
            }
        }
    }
}
