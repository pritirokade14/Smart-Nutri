import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app.dart';
import 'core/config/app_config.dart';
import 'core/observability/analytics.dart';
import 'core/theme/fonts.dart';
import 'features/settings/data/locale_store.dart';

Future<void> bootstrap() async {
  WidgetsFlutterBinding.ensureInitialized();
  registerFontLicenses();
  const config = AppConfig.fromEnvironment();
  await runWithSentry(config, () => _start(config));
}

Future<void> _start(AppConfig config) async {
  final analytics = await initAnalytics(config);
  unawaited(analytics.track('app_opened'));
  final prefs = await SharedPreferences.getInstance();
  if (config.missingRequired().isEmpty) {
    await Supabase.initialize(
      url: config.supabaseUrl,
      publishableKey: config.supabasePublishableKey,
    );
  }
  runApp(
    ProviderScope(
      overrides: [
        analyticsProvider.overrideWithValue(analytics),
        localeStoreProvider.overrideWithValue(PrefsLocaleStore(prefs)),
      ],
      child: const SmartNutriApp(),
    ),
  );
}
