package com.assetra.scan

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter

class LambdaCameraSession(
    private val onStart: ((symbology: String, rawValue: String) -> Unit) -> Unit,
    private val onStop: () -> Unit,
) : CameraScanSession {
    override fun start(onDecoded: (symbology: String, rawValue: String) -> Unit) {
        onStart(onDecoded)
    }

    override fun stop() {
        onStop()
    }
}

class CameraXMlKitSession(
    private val hasCameraPermission: () -> Boolean,
    private val onStartPipeline: ((symbology: String, rawValue: String) -> Unit) -> Unit,
    private val onStopPipeline: () -> Unit,
) : CameraScanSession {
    private var active = false

    override fun start(onDecoded: (symbology: String, rawValue: String) -> Unit) {
        if (!hasCameraPermission()) {
            return
        }
        if (active) {
            stop()
        }
        active = true
        onStartPipeline(onDecoded)
    }

    override fun stop() {
        if (!active) {
            return
        }
        onStopPipeline()
        active = false
    }
}

class DataWedgeBroadcastSession(
    private val context: Context,
    private val action: String = "com.symbol.datawedge.api.RESULT_ACTION",
    private val category: String = "android.intent.category.DEFAULT",
) : DataWedgeSession {
    private var receiver: BroadcastReceiver? = null
    private var callback: ((Map<String, String>) -> Unit)? = null

    override fun start(onIntentPayload: (Map<String, String>) -> Unit) {
        stop()
        callback = onIntentPayload

        val activeReceiver = object : BroadcastReceiver() {
            override fun onReceive(_context: Context?, intent: Intent?) {
                val payload = extractPayload(intent)
                if (payload.isNotEmpty()) {
                    callback?.invoke(payload)
                }
            }
        }

        val filter = IntentFilter(action).apply {
            addCategory(category)
        }

        context.registerReceiver(activeReceiver, filter)
        receiver = activeReceiver
    }

    override fun stop() {
        val activeReceiver = receiver ?: return
        runCatching { context.unregisterReceiver(activeReceiver) }
        receiver = null
        callback = null
    }

    private fun extractPayload(intent: Intent?): Map<String, String> {
        val extras = intent?.extras ?: return emptyMap()
        return extras.keySet().associateWith { key ->
            extras.get(key)?.toString().orEmpty()
        }
    }
}