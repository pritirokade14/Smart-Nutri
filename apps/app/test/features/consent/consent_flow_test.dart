import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/router/app_router.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/sign_in_screen.dart';
import 'package:smartnutri_ai/features/consent/data/consent_required_interceptor.dart';
import 'package:smartnutri_ai/features/consent/domain/consent_error.dart';
import 'package:smartnutri_ai/features/consent/presentation/consent_providers.dart';
import 'package:smartnutri_ai/features/consent/presentation/consent_screen.dart';
import 'package:smartnutri_ai/features/consent/presentation/policy_links.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/settings/presentation/consents_section.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_auth.dart';
import '../../support/fake_meals.dart' show mealTestOverrides;
import '../../support/fake_members.dart';

class _FakeMe implements MeClient {
  @override
  Future<MeOut> meGet() async => MeOut(
    createdAt: DateTime(2026),
    displayName: 'Asha',
    email: 'a@b.c',
    id: 'u1',
    language: MeOutLanguage.en,
  );
  @override
  Future<void> meDelete() async {}
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _FakeApi implements SmartNutriApiClient {
  _FakeApi(this.consents);
  @override
  final ConsentsClient consents;
  @override
  MeClient get me => _FakeMe();
  @override
  MembersClient get members => FakeMembersClient();
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

/// Records the errors passed on with `next`.
class _Handler extends ErrorInterceptorHandler {
  final passed = <DioException>[];
  @override
  void next(DioException err) => passed.add(err);
}

const _config = AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://x',
  supabaseUrl: 'http://s',
  supabasePublishableKey: 'k',
  googleWebClientId: 'g',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: false,
  siteUrl: 'https://smartnutri.in',
);

late ProviderContainer _container;

Future<void> _pump(
  WidgetTester t,
  FakeConsentsClient consents, {
  FakeAuthRepository? auth,
  List<Uri>? opened,
}) async {
  // Tall enough for the whole profile.
  t.view.physicalSize = const Size(900, 3000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        ...mealTestOverrides(),
        appConfigProvider.overrideWithValue(_config),
        authRepositoryProvider.overrideWithValue(
          auth ?? FakeAuthRepository(signedIn: true),
        ),
        apiClientProvider.overrideWithValue(_FakeApi(consents)),
        openExternalUrlProvider.overrideWithValue((uri) async {
          opened?.add(uri);
          return true;
        }),
      ],
      child: Consumer(
        builder: (context, ref, _) {
          _container = ProviderScope.containerOf(context);
          return MaterialApp.router(
            routerConfig: ref.watch(routerProvider),
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
          );
        },
      ),
    ),
  );
  await t.pumpAndSettle();
}

AppLocalizations _l(WidgetTester t) =>
    AppLocalizations.of(t.element(find.byType(Navigator).first));

DioException _forbidden(String path, Map<String, Object?> details) {
  final ro = RequestOptions(path: path);
  return DioException(
    requestOptions: ro,
    response: Response(
      requestOptions: ro,
      statusCode: 403,
      data: {
        'error': {
          'code': 'consent_required',
          'message_key': 'error.consent_required',
          'details': details,
        },
      },
    ),
  );
}

void main() {
  testWidgets('first_sign_in_without_terms_shows_terms_screen', (t) async {
    await _pump(t, FakeConsentsClient());
    final screen = t.widget<ConsentScreen>(find.byType(ConsentScreen));
    expect(screen.gate, isTrue);
    expect(screen.purposes, ['terms']);
    expect(find.byType(HomeScreen), findsNothing);
    expect(find.text(_l(t).consentTermsBody), findsOneWidget);
    expect(find.byKey(PolicyLinks.privacyKey), findsOneWidget);
    expect(find.byKey(PolicyLinks.termsKey), findsOneWidget);
  });

  testWidgets('consent_load_failure_blocks_with_retry_then_goes_on', (t) async {
    final consents = FakeConsentsClient(granted: {'terms'})
      ..listErrors.add(
        DioException(
          requestOptions: RequestOptions(path: '/v1/consents'),
          type: DioExceptionType.connectionError,
        ),
      );
    await _pump(t, consents);
    // Blocked: the app does not go on to home without knowing the consents.
    expect(find.byType(HomeScreen), findsNothing);
    expect(find.text(_l(t).errorNetwork), findsOneWidget);
    expect(find.text(_l(t).commonRetry), findsOneWidget);
    expect(find.byKey(ConsentScreen.declineKey), findsOneWidget);
    await t.tap(find.text(_l(t).commonRetry));
    await t.pumpAndSettle();
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('agreeing_terms_records_terms_and_goes_home', (t) async {
    final consents = FakeConsentsClient();
    await _pump(t, consents);
    await t.tap(find.byKey(ConsentScreen.agreeKey));
    await t.pumpAndSettle();
    expect(
      [for (final r in consents.recorded) (r.purpose.json, r.granted)],
      [('terms', true)],
    );
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(find.byType(ConsentScreen), findsNothing);
  });

  testWidgets('terms_needs_update_shows_terms_screen_with_update_note', (
    t,
  ) async {
    await _pump(t, FakeConsentsClient(needsUpdate: {'terms'}));
    expect(find.byType(ConsentScreen), findsOneWidget);
    expect(find.text(_l(t).consentUpdateNote), findsOneWidget);
  });

  testWidgets('policy_links_open_the_localized_web_pages', (t) async {
    final opened = <Uri>[];
    await _pump(t, FakeConsentsClient(), opened: opened);
    await t.tap(find.byKey(PolicyLinks.privacyKey));
    await t.tap(find.byKey(PolicyLinks.termsKey));
    await t.pumpAndSettle();
    expect(opened.map((u) => u.toString()), [
      'https://smartnutri.in/en/privacy',
      'https://smartnutri.in/en/terms',
    ]);
  });

  testWidgets('terms_gate_sign_out_returns_to_sign_in', (t) async {
    final auth = FakeAuthRepository(signedIn: true);
    await _pump(t, FakeConsentsClient(), auth: auth);
    await t.tap(find.byKey(ConsentScreen.declineKey));
    await t.pumpAndSettle();
    expect(auth.calls, contains('signOut'));
    expect(find.byType(SignInScreen), findsOneWidget);
  });

  testWidgets('consent_required_routes_to_consent_screen', (t) async {
    final consents = FakeConsentsClient(granted: {'terms'});
    await _pump(t, consents);
    expect(find.byType(HomeScreen), findsOneWidget);
    // What the interceptor does on a voice 403.
    _container.read(consentRequestProvider.notifier).request(['ai_processing']);
    await t.pumpAndSettle();
    final screen = t.widget<ConsentScreen>(find.byType(ConsentScreen));
    expect(screen.gate, isFalse);
    expect(screen.purposes, ['ai_processing']);
    await t.tap(find.byKey(ConsentScreen.agreeKey));
    await t.pumpAndSettle();
    expect(consents.granted, contains('ai_processing'));
    expect(find.byType(HomeScreen), findsOneWidget);
  });

  testWidgets('terms_403_reloads_consents_and_shows_terms_screen', (t) async {
    final consents = FakeConsentsClient(granted: {'terms'});
    await _pump(t, consents);
    expect(find.byType(HomeScreen), findsOneWidget);
    consents.granted.remove('terms'); // withdrawn on the web meanwhile
    final before = consents.listCalls;
    _container.read(consentRequestProvider.notifier).request(['terms']);
    await t.pumpAndSettle();
    expect(consents.listCalls, greaterThan(before));
    expect(t.widget<ConsentScreen>(find.byType(ConsentScreen)).gate, isTrue);
  });

  testWidgets('needs_update_banner_on_home_asks_again', (t) async {
    final consents = FakeConsentsClient(
      granted: {'terms'},
      needsUpdate: {'health_data'},
    );
    await _pump(t, consents);
    await t.tap(find.text(_l(t).consentReviewAgree));
    await t.pumpAndSettle();
    expect(t.widget<ConsentScreen>(find.byType(ConsentScreen)).purposes, [
      'health_data',
    ]);
    expect(find.text(_l(t).consentUpdateNote), findsOneWidget);
    await t.tap(find.byKey(ConsentScreen.agreeKey));
    await t.pumpAndSettle();
    expect(
      [for (final r in consents.recorded) (r.purpose.json, r.granted)],
      [('health_data', true)],
    );
    expect(find.text(_l(t).consentReviewAgree), findsNothing);
  });

  testWidgets('withdraw_health_consent_calls_api_and_keeps_scanning', (
    t,
  ) async {
    // Ruling G1: health_data gates only saving health fields; scanning
    // needs only terms, so the app stays usable.
    final consents = FakeConsentsClient(granted: {'terms', 'health_data'});
    await _pump(t, consents);
    await t.tap(find.text(_l(t).navProfile));
    await t.pumpAndSettle();
    await t.tap(find.byKey(ConsentsSection.actionKey('health_data')));
    await t.pumpAndSettle();
    expect(
      [for (final r in consents.recorded) (r.purpose.json, r.granted)],
      [('health_data', false)],
    );
    expect(find.byType(ProfileScreen), findsOneWidget);
    expect(find.byType(ConsentScreen), findsNothing);
  });

  testWidgets('withdraw_terms_asks_first_then_shows_terms_screen', (t) async {
    final consents = FakeConsentsClient(granted: {'terms'});
    await _pump(t, consents);
    await t.tap(find.text(_l(t).navProfile));
    await t.pumpAndSettle();
    await t.tap(find.byKey(ConsentsSection.actionKey('terms')));
    await t.pumpAndSettle();
    expect(find.text(_l(t).consentTermsWithdrawConfirm), findsOneWidget);
    expect(consents.recorded, isEmpty);
    await t.tap(find.byKey(ConsentsSection.confirmWithdrawKey));
    await t.pumpAndSettle();
    expect(
      [for (final r in consents.recorded) (r.purpose.json, r.granted)],
      [('terms', false)],
    );
    expect(t.widget<ConsentScreen>(find.byType(ConsentScreen)).gate, isTrue);
  });

  group('consent errors', () {
    test('route gate purposes and the members singular purpose', () {
      expect(
        consentPurposesOf(
          _forbidden('/v1/voice/ask', {
            'purposes': ['terms', 'ai_processing'],
          }),
        ),
        ['terms', 'ai_processing'],
      );
      expect(
        consentPurposesOf(
          _forbidden('/v1/members', {'purpose': 'health_data'}),
        ),
        ['health_data'],
      );
      expect(
        consentPurposesOf(
          DioException(requestOptions: RequestOptions(path: '/x')),
        ),
        isNull,
      );
      expect(
        isRouteConsentError(
          _forbidden('/v1/analyze', {
            'purposes': ['terms'],
          }),
        ),
        isTrue,
      );
      expect(
        isRouteConsentError(
          _forbidden('/v1/members', {'purpose': 'health_data'}),
        ),
        isFalse,
      );
    });

    test('interceptor reports gated routes but not member saves', () {
      final seen = <List<String>>[];
      final interceptor = ConsentRequiredInterceptor(seen.add);
      final gated = _Handler();
      final member = _Handler();
      final targets = _Handler();
      interceptor.onError(
        _forbidden('/v1/targets', {
          'purposes': ['health_data'],
        }),
        targets,
      );
      interceptor.onError(
        _forbidden('/v1/scans/upload-url', {
          'purposes': ['terms'],
        }),
        gated,
      );
      interceptor.onError(
        _forbidden('/v1/members/m1', {'purpose': 'health_data'}),
        member,
      );
      expect(seen, [
        ['terms'],
      ]);
      // Both errors are passed on (`next`) to reach the caller.
      expect(gated.passed, hasLength(1));
      expect(member.passed, hasLength(1));
      // Targets are handled in place (an inline consent card), no redirect.
      expect(targets.passed, hasLength(1));
    });

    testWidgets('route gate error text asks to agree; members text stays', (
      t,
    ) async {
      final l = await AppLocalizations.delegate.load(const Locale('en'));
      expect(
        localizedApiError(
          l,
          _forbidden('/v1/analyze', {
            'purposes': ['terms'],
          }),
        ),
        l.consentRequiredToContinue,
      );
      expect(
        localizedApiError(
          l,
          _forbidden('/v1/members', {'purpose': 'health_data'}),
        ),
        l.errorConsentRequired,
      );
      expect(
        localizedGatedErrorCode(l, 'consent_required'),
        l.consentRequiredToContinue,
      );
    });
  });

  test('signing out rebuilds the API client so account data is dropped', () {
    final auth = FakeAuthRepository(signedIn: true);
    final c = ProviderContainer(
      overrides: [
        appConfigProvider.overrideWithValue(_config),
        authRepositoryProvider.overrideWithValue(auth),
      ],
    );
    addTearDown(c.dispose);
    final sub = c.listen(apiClientProvider, (_, _) {});
    addTearDown(sub.close);
    final before = c.read(apiClientProvider);
    auth.setSignedIn(false);
    return Future<void>.delayed(Duration.zero, () {
      expect(identical(c.read(apiClientProvider), before), isFalse);
      expect(c.read(termsStatusProvider), TermsStatus.unknown);
    });
  });
}
