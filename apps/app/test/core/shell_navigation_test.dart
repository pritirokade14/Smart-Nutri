import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/router/app_router.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/sign_in_screen.dart';
import 'package:smartnutri_ai/features/history/presentation/history_screen.dart';
import 'package:smartnutri_ai/features/home/presentation/home_screen.dart';
import 'package:smartnutri_ai/features/members/presentation/members_list_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/label_capture_screen.dart';
import 'package:smartnutri_ai/features/scan/presentation/scan_screen.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_ai/shared/widgets/app_shell.dart';
import 'package:smartnutri_api/src/export.dart';

import '../support/fake_auth.dart';
import '../support/fake_members.dart';

class _FakeMe implements MeClient {
  @override
  Future<MeOut> meGet() async => MeOut(
    createdAt: DateTime(2026),
    displayName: 'Asha',
    email: 'a@b.c',
    id: 'u1',
    language: MeOutLanguage.values.first,
  );

  @override
  Future<void> meDelete() => throw UnimplementedError();
}

class _FakeApi implements SmartNutriApiClient {
  @override
  MeClient get me => _FakeMe();
  @override
  final MembersClient members = FakeMembersClient();
  @override
  final ConsentsClient consents = FakeConsentsClient();
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

const _cfg = AppConfig(
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

Future<FakeAuthRepository> _pump(WidgetTester t, {bool dark = false}) async {
  final repo = FakeAuthRepository(signedIn: true);
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        appConfigProvider.overrideWithValue(_cfg),
        authRepositoryProvider.overrideWithValue(repo),
        apiClientProvider.overrideWithValue(_FakeApi()),
      ],
      child: Consumer(
        builder: (context, ref, _) => MaterialApp.router(
          theme: dark ? buildDarkAppTheme() : buildAppTheme(),
          locale: const Locale('en'),
          routerConfig: ref.watch(routerProvider),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
        ),
      ),
    ),
  );
  await t.pumpAndSettle();
  return repo;
}

Finder _nav(String label) =>
    find.descendant(of: find.byType(NavigationBar), matching: find.text(label));

int _selected(WidgetTester t) =>
    t.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex;

void main() {
  testWidgets('signed-in home shows the five-tab bar with Home selected', (
    t,
  ) async {
    await _pump(t);
    expect(find.byType(AppShell), findsOneWidget);
    expect(find.byType(HomeScreen), findsOneWidget);
    for (final label in [
      en.navHome,
      en.navScan,
      en.navHistory,
      en.navFamily,
      en.navProfile,
    ]) {
      expect(_nav(label), findsOneWidget, reason: label);
    }
    expect(_selected(t), 0);
  });

  testWidgets('History is a "coming soon" tab; Family lists members; '
      'Profile shows consents', (t) async {
    await _pump(t);
    await t.tap(_nav(en.navHistory));
    await t.pumpAndSettle();
    expect(find.byType(HistoryScreen), findsOneWidget);
    expect(find.text(en.historyComingSoonTitle), findsOneWidget);
    expect(_selected(t), 2);

    await t.tap(_nav(en.navFamily));
    await t.pumpAndSettle();
    expect(find.byType(MembersListScreen), findsOneWidget);
    expect(find.text('Ravi'), findsOneWidget);
    expect(find.text(en.membersAdd), findsOneWidget);
    expect(_selected(t), 3);

    await t.tap(_nav(en.navProfile));
    await t.pumpAndSettle();
    expect(find.byType(ProfileScreen), findsOneWidget);
    expect(find.text(en.profilePrivacyTitle), findsOneWidget);
    expect(find.text(en.consentHealthDataTitle), findsOneWidget);
    expect(_selected(t), 4);

    await t.tap(_nav(en.navHome));
    await t.pumpAndSettle();
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(_selected(t), 0);
  });

  testWidgets('the Scan tab opens the full-screen scanner; back returns to '
      'the tabs', (t) async {
    await _pump(t);
    await t.tap(_nav(en.navHistory));
    await t.pumpAndSettle();
    await t.tap(_nav(en.navScan));
    await t.pump();
    await t.pump(const Duration(seconds: 1));
    expect(find.byType(ScanScreen), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    await t.pageBack();
    await t.pump();
    await t.pump(const Duration(seconds: 1));
    expect(find.byType(HistoryScreen), findsOneWidget);
    expect(_selected(t), 2);
  });

  testWidgets('home action cards open the scanner and label capture', (
    t,
  ) async {
    await _pump(t);
    expect(find.text(en.homeLabelTitle), findsOneWidget);
    await t.tap(find.text(en.homeLabelTitle));
    await t.pump();
    await t.pump(const Duration(seconds: 1));
    expect(find.byType(LabelCaptureScreen), findsOneWidget);
  });

  testWidgets('home shows the recent-scans empty state and the disclaimer', (
    t,
  ) async {
    await _pump(t);
    expect(find.text(en.homeRecentTitle), findsOneWidget);
    expect(find.text(en.homeRecentEmptyTitle), findsOneWidget);
    expect(find.text(en.commonDisclaimer), findsOneWidget);
  });

  testWidgets('sign out from Profile returns to sign-in', (t) async {
    await _pump(t);
    await t.tap(_nav(en.navProfile));
    await t.pumpAndSettle();
    await t.scrollUntilVisible(
      find.text(en.authSignOut),
      200,
      scrollable: find
          .descendant(
            of: find.byType(ProfileScreen),
            matching: find.byType(Scrollable),
          )
          .first,
    );
    await t.pumpAndSettle();
    await t.tap(find.text(en.authSignOut));
    await t.pumpAndSettle();
    expect(find.byType(SignInScreen), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
  });

  testWidgets('the shell renders in the dark theme', (t) async {
    await _pump(t, dark: true);
    expect(find.byType(HomeScreen), findsOneWidget);
    expect(t.takeException(), isNull);
  });
}
