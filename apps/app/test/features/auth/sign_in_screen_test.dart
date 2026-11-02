import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/sign_in_screen.dart';

import '../../support/fake_auth.dart';

AppConfig cfg({required bool phone}) => AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://x',
  supabaseUrl: 'http://s',
  supabasePublishableKey: 'k',
  googleWebClientId: 'g',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: phone,
);

Widget host(AppConfig c, FakeAuthRepository repo) => ProviderScope(
  overrides: [
    appConfigProvider.overrideWithValue(c),
    authRepositoryProvider.overrideWithValue(repo),
  ],
  child: const MaterialApp(
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: SignInScreen(),
  ),
);

void main() {
  testWidgets('sign-in shows Google and email, hides phone when flag off', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    await tester.pumpWidget(host(cfg(phone: false), repo));
    final l10n = AppLocalizations.of(tester.element(find.byType(SignInScreen)));
    expect(find.text(l10n.authGoogle), findsOneWidget);
    expect(find.text(l10n.authEmail), findsOneWidget);
    expect(find.text(l10n.authPhone), findsNothing);
    expect(find.text(l10n.commonDisclaimer), findsOneWidget);
    await tester.tap(find.text(l10n.authGoogle));
    await tester.pump();
    expect(repo.calls, ['google']);
  });

  testWidgets('sign-in shows phone when flag on', (tester) async {
    await tester.pumpWidget(host(cfg(phone: true), FakeAuthRepository()));
    final l10n = AppLocalizations.of(tester.element(find.byType(SignInScreen)));
    expect(find.text(l10n.authPhone), findsOneWidget);
  });
}
