import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';
import 'package:smartnutri_ai/core/router/app_router.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';

import '../../support/fake_auth.dart';
import '../../support/fake_meals.dart';
import '../../support/fake_user_types.dart';

const testAppConfig = AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://x',
  supabaseUrl: 'http://s',
  supabasePublishableKey: 'k',
  googleWebClientId: 'g',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: false,
  featureEmailOtp: false,
);

final en = lookupAppLocalizations(const Locale('en'));

class AppHarness {
  AppHarness(this.api);
  final FakeUserTypesApi api;
  final events = <String>[];
  late ProviderContainer container;

  GoRouter get router => container.read(routerProvider);
}

/// Pumps the whole signed-in app (router, shell) over [api], on a tall
/// surface. Analytics events are recorded in [AppHarness.events].
Future<AppHarness> pumpApp(
  WidgetTester t,
  FakeUserTypesApi api, {
  FakeMealsClient? meals,
  String? initial,
  List<Override> overrides = const [],
  String locale = 'en',
  Size size = const Size(900, 3600),
}) async {
  t.view.physicalSize = size;
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final h = AppHarness(api);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        ...mealTestOverrides(client: meals ?? FakeMealsClient()),
        ...overrides,
        appConfigProvider.overrideWithValue(testAppConfig),
        authRepositoryProvider.overrideWithValue(
          FakeAuthRepository(signedIn: true),
        ),
        apiClientProvider.overrideWithValue(api),
        analyticsProvider.overrideWithValue(
          Analytics((e, _) async => h.events.add(e)),
        ),
      ],
      child: Consumer(
        builder: (context, ref, _) {
          h.container = ProviderScope.containerOf(context);
          return MaterialApp.router(
            theme: buildAppTheme(),
            locale: Locale(locale),
            routerConfig: ref.watch(routerProvider),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
          );
        },
      ),
    ),
  );
  await t.pumpAndSettle();
  if (initial != null) {
    h.router.go(initial);
    await t.pumpAndSettle();
  }
  return h;
}
