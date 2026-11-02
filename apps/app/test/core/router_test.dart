import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/router/app_router.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/phone_otp_screen.dart';
import 'package:smartnutri_ai/features/auth/presentation/sign_in_screen.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/scan_screen.dart';
import 'package:smartnutri_api/src/export.dart';

import '../support/fake_auth.dart';

class _FakeMe implements MeClient {
  _FakeMe(this.result);
  final Future<MeOut> Function() result;
  @override
  Future<MeOut> meGet() => result();
}

class _FakeApi implements SmartNutriApiClient {
  _FakeApi(this._me);
  final MeClient _me;
  @override
  MeClient get me => _me;
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

AppConfig _cfg(bool phone) => AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://x',
  supabaseUrl: 'http://s',
  supabasePublishableKey: 'k',
  googleWebClientId: 'g',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: phone,
);

Widget _app(FakeAuthRepository repo, MeClient me, {bool phone = false}) =>
    ProviderScope(
      overrides: [
        appConfigProvider.overrideWithValue(_cfg(phone)),
        authRepositoryProvider.overrideWithValue(repo),
        apiClientProvider.overrideWithValue(_FakeApi(me)),
      ],
      child: Consumer(
        builder: (context, ref, _) => MaterialApp.router(
          routerConfig: ref.watch(routerProvider),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
        ),
      ),
    );

MeOut _me() => MeOut(
  createdAt: DateTime(2026),
  displayName: 'Asha',
  email: 'a@b.c',
  id: 'u1',
  language: MeOutLanguage.values.first,
);

void main() {
  testWidgets('signed-out user is redirected to /sign-in', (tester) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(), _FakeMe(() async => _me())),
    );
    await tester.pumpAndSettle();
    expect(find.byType(SignInScreen), findsOneWidget);
    expect(find.byType(HomeScreen), findsNothing);
  });

  testWidgets('signed-in user lands on home with name and disclaimer', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(signedIn: true), _FakeMe(() async => _me())),
    );
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(HomeScreen)));
    expect(find.text(l10n.homeWelcome('Asha')), findsOneWidget);
    expect(find.text(l10n.commonDisclaimer), findsOneWidget);
  });

  testWidgets('home scan button navigates to /scan', (tester) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(signedIn: true), _FakeMe(() async => _me())),
    );
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(HomeScreen)));
    await tester.tap(find.text(l10n.homeScanCta));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(find.byType(ScanScreen), findsOneWidget);
  });

  testWidgets('API error maps to error string; sign-out returns to sign-in', (
    tester,
  ) async {
    final repo = FakeAuthRepository(signedIn: true);
    final ro = RequestOptions(path: '/v1/me');
    await tester.pumpWidget(
      _app(
        repo,
        _FakeMe(
          () async => throw DioException(
            requestOptions: ro,
            response: Response(
              requestOptions: ro,
              statusCode: 429,
              data: {
                'error': {
                  'code': 'rate_limited',
                  'message_key': 'error.rate_limited',
                },
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final l10n = AppLocalizations.of(tester.element(find.byType(HomeScreen)));
    expect(find.text(l10n.errorRateLimited), findsOneWidget);
    await tester.tap(find.text(l10n.authSignOut));
    await tester.pumpAndSettle();
    expect(find.byType(SignInScreen), findsOneWidget);
  });

  testWidgets('phone route absent when flag off', (tester) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(), _FakeMe(() async => _me())),
    );
    await tester.pumpAndSettle();
    GoRouter.of(tester.element(find.byType(SignInScreen))).go('/sign-in/phone');
    await tester.pumpAndSettle();
    expect(find.byType(PhoneOtpScreen), findsNothing);
    expect(find.byType(HomeScreen), findsNothing);
  });

  testWidgets('phone route present when flag on', (tester) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(), _FakeMe(() async => _me()), phone: true),
    );
    await tester.pumpAndSettle();
    GoRouter.of(tester.element(find.byType(SignInScreen))).go('/sign-in/phone');
    await tester.pumpAndSettle();
    expect(find.byType(PhoneOtpScreen), findsOneWidget);
  });

  testWidgets('signed-in user going to /sign-in lands on /home', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(FakeAuthRepository(signedIn: true), _FakeMe(() async => _me())),
    );
    await tester.pumpAndSettle();
    GoRouter.of(tester.element(find.byType(HomeScreen))).go('/sign-in');
    await tester.pumpAndSettle();
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(find.byType(SignInScreen), findsNothing);
  });
}
