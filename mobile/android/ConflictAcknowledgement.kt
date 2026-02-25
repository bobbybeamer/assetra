package com.assetra.sync

data class ConflictAcknowledgement(
    val conflictId: String,
    val resolution: String,
    val resolvedAt: String,
)
