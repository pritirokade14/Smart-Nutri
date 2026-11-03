import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/app.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/sign_in_screen.dart';
import 'package:smartnutri_ai/features/methodology/presentation/methodology_screen.dart';
import 'package:smartnutri_ai/features/settings/data/locale_store.dart';
import 'package:smartnutri_ai/features/settings/presentation/delete_account_dialog.dart';
import 'package:smartnutri_ai/features/settings/presentation/goodbye_screen.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_auth.dart';
import '../../support/fake_meals.dart' show MemoryMealQueue, mealTestOverrides;
import '../../support/fake_members.dart';
import '../members/members_harness.dart' show apiError, l10nFor;

class _FakeMe implements MeClient {
  /// Thrown by the next deletes, in order.
  final errors = <Object>[];
  int deleteCalls = 0;

  @override
  Future<MeOut> meGet() async => MeOut(
    createdAt: DateTime(2026),
    displayName: 'Asha',
    email: 'a@b.c',
    id: 'u1',
    language: MeOutLanguage.en,
  );

  @override
  Future<void> meDelete() async {
    deleteCalls++;
    if (errors.isNotEmpty) throw errors.removeAt(0);
  }
}

class _FakeApi implements SmartNutriApiClient {
  _FakeApi(this.me);
  @override
  final MeClient me;
  @override
  final ConsentsClient consents = FakeConsentsClient(granted: {'terms'});
  @override
  MembersClient get members => FakeMembersClient();
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
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

PendingMeal _pending() => PendingMeal(
  clientId: 'c1',
  memberId: 'm1',
  productId: 'p1',
  grams: 30,
  eatenAt: DateTime.utc(2026, 11, 3, 8),
  attempts: 0,
);

class _Harness {
  final me = _FakeMe();
  final auth = FakeAuthRepository(signedIn: true);
  final store = MemoryLocaleStore();
  final queue = MemoryMealQueue();
  final events = <String>[];
  final opened = <Uri>[];
}

Future<_Harness> _openProfile(WidgetTester t) async {
  t.view.physicalSize = const Size(900, 3000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final h = _Harness();
  h.queue.onClearAll = () => h.auth.calls.add('clearAll');
  await h.queue.add(_pending());
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        ...mealTestOverrides(queue: h.queue),
        appConfigProvider.overrideWithValue(_config),
        authRepositoryProvider.overrideWithValue(h.auth),
        apiClientProvider.overrideWithValue(_FakeApi(h.me)),
        localeStoreProvider.overrideWithValue(h.store),
        analyticsProvider.overrideWithValue(
          Analytics((e, _) async => h.events.add(e)),
        ),
        openExternalUrlProvider.overrideWithValue((uri) async {
          h.opened.add(uri);
          return true;
        }),
      ],
      child: const SmartNutriApp(),
    ),
  );
  await t.pumpAndSettle();
  await t.tap(find.text(l10nFor('en').navProfile));
  await t.pumpAndSettle();
  expect(find.byType(ProfileScreen), findsOneWidget);
  return h;
}

Future<void> _openDeleteDialog(WidgetTester t) async {
  await t.tap(find.byKey(ProfileScreen.deleteKey));
  await t.pumpAndSettle();
  expect(find.byType(DeleteAccountDialog), findsOneWidget);
}

bool _confirmEnabled(WidgetTester t) =>
    t.widget<FilledButton>(find.byKey(DeleteAccountDialog.confirmKey)).enabled;

void main() {
  final l = l10nFor('en');

  testWidgets('profile shows language, consents, policies and account', (
    t,
  ) async {
    final h = await _openProfile(t);
    expect(find.text(l.languageLabel), findsWidgets);
    expect(find.text(l.profilePrivacyTitle), findsOneWidget);
    expect(find.text(l.settingsAboutTitle), findsOneWidget);
    expect(find.text(l.authSignOut), findsOneWidget);
    expect(find.text(l.profileComingSoonTitle), findsNothing);
    await t.tap(find.byKey(ProfileScreen.privacyKey));
    await t.pumpAndSettle();
    expect(h.opened.single.toString(), 'https://smartnutri.in/en/privacy');
  });

  testWidgets('choosing_language_switches_app_locale_and_persists', (t) async {
    final h = await _openProfile(t);
    await t.tap(find.byKey(ProfileScreen.languageKey('hi')));
    await t.pumpAndSettle();
    expect(h.store.read(), 'hi');
    expect(find.text(l10nFor('hi').profileTitle), findsWidgets);
    await t.tap(find.byKey(ProfileScreen.languageKey(null)));
    await t.pumpAndSettle();
    expect(h.store.read(), isNull);
    expect(find.text(l.profileTitle), findsWidgets);
  });

  testWidgets('delete_requires_typed_confirmation', (t) async {
    final h = await _openProfile(t);
    await _openDeleteDialog(t);
    expect(find.text(l.settingsDeleteBody), findsOneWidget);
    expect(_confirmEnabled(t), isFalse);
    await t.enterText(find.byKey(DeleteAccountDialog.inputKey), 'DELET');
    await t.pump();
    expect(_confirmEnabled(t), isFalse);
    await t.enterText(find.byKey(DeleteAccountDialog.inputKey), ' DELETE ');
    await t.pump();
    expect(_confirmEnabled(t), isTrue);
    // Cancel deletes nothing.
    await t.tap(find.text(l.commonCancel));
    await t.pumpAndSettle();
    expect(h.me.deleteCalls, 0);
    expect(find.byType(ProfileScreen), findsOneWidget);
  });

  testWidgets('delete_success_signs_out', (t) async {
    final h = await _openProfile(t);
    await _openDeleteDialog(t);
    await t.enterText(find.byKey(DeleteAccountDialog.inputKey), 'DELETE');
    await t.pump();
    await t.tap(find.byKey(DeleteAccountDialog.confirmKey));
    await t.pumpAndSettle();
    expect(h.me.deleteCalls, 1);
    expect(h.auth.calls, contains('signOut'));
    expect(
      h.auth.calls.indexOf('clearAll'),
      lessThan(h.auth.calls.indexOf('signOut')),
    );
    expect(h.queue.rows, isEmpty);
    expect(h.events, ['account_deleted']);
    expect(find.byType(GoodbyeScreen), findsOneWidget);
    expect(find.text(l.goodbyeTitle), findsOneWidget);
    await t.tap(find.text(l.goodbyeAction));
    await t.pumpAndSettle();
    expect(find.byType(SignInScreen), findsOneWidget);
  });

  testWidgets('sign_out_clears_the_offline_log_first', (t) async {
    final h = await _openProfile(t);
    expect(h.queue.rows, isNotEmpty);
    await t.tap(find.text(l.authSignOut));
    await t.pumpAndSettle();
    expect(h.auth.calls, ['clearAll', 'signOut']);
    expect(h.queue.rows, isEmpty);
  });

  testWidgets('delete_503_shows_retry', (t) async {
    final h = await _openProfile(t);
    h.me.errors.add(apiError(503, 'deletion_incomplete'));
    await _openDeleteDialog(t);
    await t.enterText(find.byKey(DeleteAccountDialog.inputKey), 'DELETE');
    await t.pump();
    await t.tap(find.byKey(DeleteAccountDialog.confirmKey));
    await t.pumpAndSettle();
    expect(find.text(l.errorDeletionIncomplete), findsOneWidget);
    expect(h.auth.calls, isNot(contains('signOut')));
    expect(h.queue.rows, isNotEmpty);
    expect(
      find.descendant(
        of: find.byKey(DeleteAccountDialog.confirmKey),
        matching: find.text(l.commonRetry),
      ),
      findsOneWidget,
    );
    await t.tap(find.byKey(DeleteAccountDialog.confirmKey));
    await t.pumpAndSettle();
    expect(h.me.deleteCalls, 2);
    expect(find.byType(GoodbyeScreen), findsOneWidget);
  });

  testWidgets('how we score opens from the profile', (t) async {
    await _openProfile(t);
    await t.tap(find.byKey(ProfileScreen.methodologyKey));
    await t.pumpAndSettle();
    expect(find.byType(MethodologyScreen), findsOneWidget);
  });

  test('prefs locale store keeps the choice', () async {
    final store = MemoryLocaleStore();
    expect(store.read(), isNull);
    await store.write('mr');
    expect(store.read(), 'mr');
    await store.write(null);
    expect(store.read(), isNull);
  });
}
