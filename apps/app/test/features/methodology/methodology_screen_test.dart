import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/theme/app_theme.dart';
import 'package:smartnutri_ai/features/methodology/data/methodology_repository.dart';
import 'package:smartnutri_ai/features/methodology/presentation/methodology_providers.dart';
import 'package:smartnutri_ai/features/methodology/presentation/methodology_screen.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';

class _FakeMethodology implements MethodologyClient {
  _FakeMethodology(this.result);
  Future<Methodology> Function() result;
  final languages = <MethodologyLanguage?>[];

  @override
  Future<Methodology> methodologyGet({
    MethodologyLanguage? language = MethodologyLanguage.en,
  }) {
    languages.add(language);
    return result();
  }
}

DioException _network() =>
    DioException(requestOptions: RequestOptions(path: '/v1/methodology'));

Future<List<Uri>> _pump(WidgetTester t, _FakeMethodology client) async {
  t.view.physicalSize = const Size(900, 6000);
  t.view.devicePixelRatio = 1;
  addTearDown(t.view.reset);
  final opened = <Uri>[];
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        methodologyRepositoryProvider.overrideWithValue(
          MethodologyRepository(client),
        ),
        openExternalUrlProvider.overrideWithValue((uri) async {
          opened.add(uri);
          return true;
        }),
      ],
      child: MaterialApp(
        theme: buildAppTheme(),
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: const MethodologyScreen(),
      ),
    ),
  );
  await t.pumpAndSettle();
  return opened;
}

AppLocalizations get _l => lookupAppLocalizations(const Locale('en'));

void main() {
  testWidgets(
    'methodology_screen_renders_rules_from_fixture_and_pending_review_banner',
    (t) async {
      final fixture = methodologyFixture();
      final client = _FakeMethodology(() async => fixture);
      await _pump(t, client);
      expect(client.languages, [MethodologyLanguage.en]);
      expect(find.text(_l.methodologyPendingReview), findsOneWidget);
      expect(find.text(_l.methodologyIntro), findsOneWidget);
      expect(find.text(_l.methodologySectionHighInTitle), findsOneWidget);
      expect(find.text(_l.methodologySectionBloodSugarTitle), findsOneWidget);
      expect(find.text(_l.methodologyVersion(fixture.version)), findsOneWidget);
      expect(find.text(_l.commonDisclaimer), findsOneWidget);
      // The live sugar threshold for "high in" (food), straight from the API.
      final highIn = find.byKey(MethodologyScreen.sectionKey('high_in'));
      await t.tap(
        find.descendant(
          of: highIn,
          matching: find.text(_l.methodologyValuesTitle),
        ),
      );
      await t.pumpAndSettle();
      expect(
        find.descendant(of: highIn, matching: find.text('food › sugars_g')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: highIn, matching: find.text('22.5')),
        findsOneWidget,
      );
    },
  );

  testWidgets('sources_show_as_unverified_links', (t) async {
    final fixture = methodologyFixture();
    final opened = await _pump(t, _FakeMethodology(() async => fixture));
    final first = fixture.sources.first;
    expect(first.urlVerified, isFalse);
    expect(find.text(first.title), findsOneWidget);
    expect(
      find.text(_l.methodologyUrlUnverified),
      findsNWidgets(
        fixture.sources.where((s) => !s.urlVerified && s.url != null).length,
      ),
    );
    await t.tap(find.text(first.url!));
    await t.pumpAndSettle();
    expect(opened.single.toString(), first.url);
  });

  testWidgets('no_pending_banner_when_signed_off', (t) async {
    final json = methodologyFixture().toJson()
      ..['pending_clinician_review'] = false;
    await _pump(t, _FakeMethodology(() async => Methodology.fromJson(json)));
    expect(find.text(_l.methodologyPendingReview), findsNothing);
  });

  testWidgets('error_state_retries', (t) async {
    final fixture = methodologyFixture();
    final client = _FakeMethodology(() async => throw _network());
    await _pump(t, client);
    expect(find.text(_l.errorNetwork), findsOneWidget);
    client.result = () async => fixture;
    await t.tap(find.text(_l.commonRetry));
    await t.pumpAndSettle();
    expect(find.text(_l.methodologySectionHighInTitle), findsOneWidget);
  });

  test('methodology is cached in memory for an hour', () async {
    final fixture = methodologyFixture();
    final client = _FakeMethodology(() async => fixture);
    final c = ProviderContainer(
      overrides: [
        methodologyRepositoryProvider.overrideWithValue(
          MethodologyRepository(client),
        ),
      ],
    );
    addTearDown(c.dispose);
    final sub = c.listen(methodologyProvider('hi'), (_, _) {});
    await c.read(methodologyProvider('hi').future);
    sub.close();
    await Future<void>.delayed(Duration.zero);
    await c.read(methodologyProvider('hi').future);
    expect(client.languages, [MethodologyLanguage.hi]);
  });

  test('thresholdRows flattens nested values as the API sent them', () {
    expect(
      thresholdRows({
        'food': {'sugars_g': 22.5, 'salt_g': 1.5},
        'applies_to': ['diabetes', 'pcos'],
        'grades': [
          {'grade': 'A', 'max_points': 0},
        ],
        'max_age': 13,
        'avoid': 5.0,
      }),
      [
        ('food › sugars_g', '22.5'),
        ('food › salt_g', '1.5'),
        ('applies_to', 'diabetes, pcos'),
        ('grades', 'grade: A, max_points: 0'),
        ('max_age', '13'),
        ('avoid', '5'),
      ],
    );
  });
}
