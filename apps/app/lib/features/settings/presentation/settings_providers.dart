import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/locale_store.dart';

/// The app's languages, in the order the picker shows them.
const appLanguageCodes = ['en', 'hi', 'mr'];

/// The language the user chose, or null to follow the device.
class AppLocaleNotifier extends Notifier<Locale?> {
  @override
  Locale? build() {
    final code = ref.watch(localeStoreProvider).read();
    return appLanguageCodes.contains(code) ? Locale(code!) : null;
  }

  Future<void> select(String? code) async {
    final valid = appLanguageCodes.contains(code) ? code : null;
    await ref.read(localeStoreProvider).write(valid);
    state = valid == null ? null : Locale(valid);
  }
}

final appLocaleProvider = NotifierProvider<AppLocaleNotifier, Locale?>(
  AppLocaleNotifier.new,
);
