plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.assetra.sample"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.assetra.sample"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    sourceSets {
        getByName("main") {
            java.srcDirs("../../android")
            manifest.srcFile("src/main/AndroidManifest.xml")
            res.srcDirs("src/main/res")
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")

    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    implementation("androidx.camera:camera-core:1.3.4")
    implementation("androidx.camera:camera-camera2:1.3.4")
    implementation("androidx.camera:camera-lifecycle:1.3.4")
    implementation("androidx.camera:camera-view:1.3.4")
    implementation("com.google.mlkit:barcode-scanning:17.2.0")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    implementation(name = "API3_ASCII-release-2.0.5.238", ext = "aar")
    implementation(name = "API3_CMN-release-2.0.5.238", ext = "aar")
    implementation(name = "API3_INTERFACE-release-2.0.5.238", ext = "aar")
    implementation(name = "API3_LLRP-release-2.0.5.238", ext = "aar")
    implementation(name = "API3_NGE-Transportrelease-2.0.5.238", ext = "aar")
    implementation(name = "API3_NGE-protocolrelease-2.0.5.238", ext = "aar")
    implementation(name = "API3_NGEUSB-Transportrelease-2.0.5.238", ext = "aar")
    implementation(name = "API3_READER-release-2.0.5.238", ext = "aar")
    implementation(name = "API3_TRANSPORT-release-2.0.5.238", ext = "aar")
    implementation(name = "rfidhostlib", ext = "aar")
    implementation(name = "rfidseriallib", ext = "aar")
}
