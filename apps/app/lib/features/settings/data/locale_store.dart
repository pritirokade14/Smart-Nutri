import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Where the chosen app language (`en`, `hi`, `mr`, or null for the device
/// language) is kept. A device preference, not account data: it stays after
/// sign-out and account deletion.
abstract interface class LocaleStore {
  String? read();
  Future<void> write(String? code);
}

/// Keeps the choice for this run only (tests, and before bootstrap).
class MemoryLocaleStore implements LocaleStore {
  String? _code;

  @override
  String? read() => _code;

  @override
  Future<void> write(String? code) async => _code = code;
}

/// Keeps the choice on the device.
class PrefsLocaleStore implements LocaleStore {
  PrefsLocaleStore(this._prefs);

  static const _key = 'app_locale';
  final SharedPreferences _prefs;

  @override
  String? read() => _prefs.getString(_key);

  @override
  Future<void> write(String? code) async {
    if (code == null) {
      await _prefs.remove(_key);
    } else {
      await _prefs.setString(_key, code);
    }
  }
}

/// Overridden in bootstrap with a [PrefsLocaleStore].
final localeStoreProvider = Provider<LocaleStore>((ref) => MemoryLocaleStore());
