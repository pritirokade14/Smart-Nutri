package com.smartnutri.app

import android.content.Intent
import android.net.Uri
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "openAppSettings" -> {
                        val intent = Intent(
                            Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.fromParts("package", packageName, null),
                        )
                        try {
                            startActivity(intent)
                            result.success(null)
                        } catch (e: Exception) {
                            result.error("unavailable", "Cannot open settings", null)
                        }
                    }
                    "shouldShowRationale" -> {
                        val permission = call.argument<String>("permission")
                        if (permission == null) {
                            result.error("bad_args", "permission is required", null)
                        } else {
                            result.success(shouldShowRequestPermissionRationale(permission))
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    companion object {
        private const val CHANNEL = "com.smartnutri.app/app_settings"
    }
}
