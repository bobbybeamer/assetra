package com.assetra.sync

data class ConflictRecord(
    val id: String,
    val assetId: String,
    val field: String,
    val localValue: String,
    val serverValue: String,
    val updatedAt: String,
)
