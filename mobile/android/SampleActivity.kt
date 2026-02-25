package com.assetra.sample

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Toast
import android.content.Intent

import com.assetra.conflicts.ConflictResolutionActivity

class SampleActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val baseUrlInput = EditText(this).apply { hint = "Base URL" }
        val tenantInput = EditText(this).apply { hint = "Tenant ID" }
        val usernameInput = EditText(this).apply { hint = "Username" }
        val passwordInput = EditText(this).apply { hint = "Password" }
        val runButton = Button(this).apply { text = "Run Sync Sample" }
        val conflictsButton = Button(this).apply { text = "View Conflicts" }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(baseUrlInput)
            addView(tenantInput)
            addView(usernameInput)
            addView(passwordInput)
            addView(runButton)
            addView(conflictsButton)
        }
        setContentView(layout)

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
                SampleAppRunner.runSample(
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
}
