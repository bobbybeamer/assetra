pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        flatDir {
            dirs("../android/vendor/Zebra/RFIDAPI3_SDK_2.0.5.238")
        }
    }
}

rootProject.name = "AssetraAndroidApp"
include(":app")
