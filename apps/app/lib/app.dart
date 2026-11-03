import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/config/app_config.dart';
import 'core/l10n/app_localizations.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

class SmartNutriApp extends ConsumerWidget {
  const SmartNutriApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Without Supabase config (e.g. a bare build) the auth stack cannot start,
    // so show the plain shell instead of crashing.
    final configured = ref.watch(appConfigProvider).missingRequired().isEmpty;
    if (!configured) {
      return MaterialApp(
        onGenerateTitle: (context) => AppLocalizations.of(context).appName,
        theme: buildAppTheme(),
        darkTheme: buildDarkAppTheme(),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(
          body: Center(
            child: Builder(
              builder: (context) => Text(AppLocalizations.of(context).appName),
            ),
          ),
        ),
      );
    }
    return MaterialApp.router(
      onGenerateTitle: (context) => AppLocalizations.of(context).appName,
      theme: buildAppTheme(),
      darkTheme: buildDarkAppTheme(),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      routerConfig: ref.watch(routerProvider),
    );
  }
}
