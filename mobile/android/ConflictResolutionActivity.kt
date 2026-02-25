package com.assetra.conflicts

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

import com.assetra.sync.ConflictRecord
import com.assetra.sync.SampleStoreHolder
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class ConflictResolutionActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }


        val localStore = SampleStoreHolder.store
        if (localStore.pendingConflicts().isEmpty()) {
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
        }
        val conflicts = localStore.pendingConflicts().toMutableList()

        fun renderConflicts() {
            layout.removeAllViews()
            if (conflicts.isEmpty()) {
                val empty = TextView(this).apply { text = "No conflicts" }
                layout.addView(empty)
                return
            }

            for (conflict in conflicts) {
                val title = TextView(this).apply {
                    text = "Asset ${conflict.assetId} (${conflict.field})"
                }
                val values = TextView(this).apply {
                    text = "Local: ${conflict.localValue} | Server: ${conflict.serverValue}"
                }
                val acceptServer = Button(this).apply { text = "Accept Server" }
                val keepLocal = Button(this).apply { text = "Keep Local" }

                acceptServer.setOnClickListener {
                    CoroutineScope(Dispatchers.Main).launch {
                        localStore.resolveConflict(conflict.id, useServerValue = true)
                        conflicts.removeAll { it.id == conflict.id }
                        renderConflicts()
                    }
                }
                keepLocal.setOnClickListener {
                    CoroutineScope(Dispatchers.Main).launch {
                        localStore.resolveConflict(conflict.id, useServerValue = false)
                        conflicts.removeAll { it.id == conflict.id }
                        renderConflicts()
                    }
                }

                layout.addView(title)
                layout.addView(values)
                layout.addView(acceptServer)
                layout.addView(keepLocal)
            }
        }

        renderConflicts()

        setContentView(layout)
    }
}
