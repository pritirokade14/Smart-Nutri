import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// The Android permissions the app asks for at the moment of use.
const cameraPermission = 'android.permission.CAMERA';
const microphonePermission = 'android.permission.RECORD_AUDIO';

/// Opens the app's system settings screen and tells whether a denied
/// permission can still be asked for, through the MainActivity method
/// channel (no extra package).
///
/// A permission counts as permanently denied when it was denied twice, or
/// when it was denied once and Android no longer shows the request rationale
/// (the user chose "don't ask again").
class AppSettings {
  AppSettings({MethodChannel? channel})
    : _channel = channel ?? const MethodChannel(channelName);

  static const channelName = 'com.smartnutri.app/app_settings';

  final MethodChannel _channel;
  final _denials = <String, int>{};

  /// Records one denial of [permission]; true when it is now permanently
  /// denied.
  Future<bool> noteDenied(String permission) async {
    final count = (_denials[permission] ?? 0) + 1;
    _denials[permission] = count;
    if (count >= 2) return true;
    return !await shouldShowRationale(permission);
  }

  /// Android's `shouldShowRequestPermissionRationale`. Unknown (no platform
  /// side, for example in tests) is treated as "can still ask".
  Future<bool> shouldShowRationale(String permission) async {
    try {
      return await _channel.invokeMethod<bool>('shouldShowRationale', {
            'permission': permission,
          }) ??
          true;
    } on PlatformException {
      return true;
    } on MissingPluginException {
      return true;
    }
  }

  /// Opens `android.settings.APPLICATION_DETAILS_SETTINGS` for this app.
  Future<void> open() async {
    try {
      await _channel.invokeMethod<void>('openAppSettings');
    } on PlatformException {
      // Nothing more to do; the user can open Settings by hand.
    } on MissingPluginException {
      // Not on Android.
    }
  }
}

final appSettingsProvider = Provider<AppSettings>((ref) => AppSettings());
