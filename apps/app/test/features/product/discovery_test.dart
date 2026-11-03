import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/network/api_client.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/product/data/product_discovery_repository.dart';
import 'package:smartnutri_ai/features/product/presentation/alternatives_section.dart';
import 'package:smartnutri_ai/features/product/presentation/compare_screen.dart';
import 'package:smartnutri_ai/features/product/presentation/discovery_routes.dart';
import 'package:smartnutri_ai/features/product/presentation/search_screen.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_ai/shared/widgets/verdict_badge.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_products.dart';
import '../../support/fixtures.dart';

final en = lookupAppLocalizations(const Locale('en'));

class _Api implements SmartNutriApiClient {
  _Api(this.products);
  @override
  final ProductsClient products;
  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

/// The widget at `/`; other routes show their location so navigation can be
/// asserted.
Future<void> _pump(
  WidgetTester t,
  FakeProductsClient api,
  Widget home, {
  List<Uri>? opened,
}) async {
  final router = GoRouter(
    routes: [
      GoRoute(path: '/', builder: (_, _) => home),
      for (final p in ['/compare', '/result', '/search'])
        GoRoute(
          path: p,
          builder: (_, s) => Scaffold(body: Text('at ${s.uri}')),
        ),
    ],
  );
  await t.pumpWidget(
    ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(_Api(api)),
        openExternalUrlProvider.overrideWithValue((uri) async {
          opened?.add(uri);
          return true;
        }),
      ],
      child: MaterialApp.router(
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        routerConfig: router,
      ),
    ),
  );
  await t.pumpAndSettle();
}

Widget _section(ProductRef ref, List<VerdictOut> verdicts) => Scaffold(
  body: SingleChildScrollView(
    child: AlternativesSection(product: ref, verdicts: verdicts),
  ),
);

void main() {
  final verdicts = analyzeFixture('sf_biscuit').verdicts;

  group('AlternativesSection', () {
    testWidgets('renders API items with grade, member status and OFF credit; '
        'never an avoid for the member', (t) async {
      final api = FakeProductsClient()
        ..alternativesOut = AlternativesOut(
          items: [
            alternative(
              name: 'Oat Biscuit',
              barcode: '111',
              grade: NutriScoreGrade.a,
              memberStatus: MemberStatus.ok,
            ),
            alternative(
              name: 'Never Shown',
              barcode: '222',
              memberStatus: MemberStatus.avoid,
            ),
            alternative(
              name: 'Ragi Cookie',
              productId: 'p9',
              sugarsG: null,
              memberStatus: MemberStatus.unknown,
            ),
          ],
          reason: AlternativesOutReason.ok,
        );
      final opened = <Uri>[];
      await _pump(
        t,
        api,
        _section((productId: 'src', barcode: null), verdicts),
        opened: opened,
      );

      expect(api.alternativesCalls.single, (
        'src',
        null,
        verdicts.first.memberId,
      ));
      expect(find.text(en.alternativesTitle), findsOneWidget);
      expect(find.text(en.alternativesSubtitle), findsOneWidget);
      expect(find.text('Oat Biscuit'), findsOneWidget);
      expect(find.text('Ragi Cookie'), findsOneWidget);
      expect(find.text('Never Shown'), findsNothing);
      expect(find.text(en.alternativesSugars('4')), findsOneWidget);
      // Status badges exactly as the API sent them; unknown is grey.
      final badges = t.widgetList<VerdictBadge>(find.byType(VerdictBadge));
      expect(badges.map((b) => b.status).toList(), ['ok', 'unknown']);
      // OFF data is credited.
      expect(find.byType(OffAttribution), findsOneWidget);
    });

    testWidgets('picking another member asks the API for that member', (
      t,
    ) async {
      final api = FakeProductsClient();
      await _pump(
        t,
        api,
        _section((productId: null, barcode: '890'), verdicts),
      );
      final other = verdicts[2];
      await t.ensureVisible(find.text(other.memberName).first);
      await t.tap(find.text(other.memberName).first);
      await t.pumpAndSettle();
      expect(api.alternativesCalls.last, (null, '890', other.memberId));
    });

    for (final (reason, text) in [
      (AlternativesOutReason.noCategory, en.alternativesReasonNoCategory),
      (AlternativesOutReason.noBetterFound, en.alternativesReasonNoBetterFound),
      (
        AlternativesOutReason.sourceUngraded,
        en.alternativesReasonSourceUngraded,
      ),
      (AlternativesOutReason.ok, en.alternativesReasonNoBetterFound),
    ]) {
      testWidgets('empty list explains why ($reason)', (t) async {
        final api = FakeProductsClient()
          ..alternativesOut = AlternativesOut(items: const [], reason: reason);
        await _pump(
          t,
          api,
          _section((productId: 'src', barcode: null), verdicts),
        );
        expect(find.text(text), findsOneWidget);
      });
    }

    testWidgets('error with retry', (t) async {
      final api = FakeProductsClient()
        ..alternativesError = apiError(503, 'off_unavailable');
      await _pump(
        t,
        api,
        _section((productId: 'src', barcode: null), verdicts),
      );
      expect(find.text(en.errorOffUnavailable), findsOneWidget);
      api.alternativesError = null;
      await t.tap(find.text(en.commonRetry));
      await t.pumpAndSettle();
      expect(find.text(en.alternativesReasonNoBetterFound), findsOneWidget);
    });

    testWidgets('Compare opens the side-by-side view', (t) async {
      final api = FakeProductsClient()
        ..alternativesOut = AlternativesOut(
          items: [alternative(name: 'Oat Biscuit', barcode: '111')],
          reason: AlternativesOutReason.ok,
        );
      await _pump(
        t,
        api,
        _section((productId: 'src', barcode: null), verdicts),
      );
      await t.ensureVisible(find.text(en.alternativesCompare));
      await t.tap(find.text(en.alternativesCompare));
      await t.pumpAndSettle();
      expect(
        find.text(
          'at /compare?a=src&b_barcode=111&member_id=${verdicts.first.memberId}',
        ),
        findsOneWidget,
      );
    });
  });

  group('SearchScreen', () {
    testWidgets('asks for 3+ letters before searching', (t) async {
      final api = FakeProductsClient();
      await _pump(t, api, const SearchScreen());
      await t.enterText(find.byType(TextField), 'ab');
      await t.pump(const Duration(milliseconds: 700));
      expect(find.text(en.searchTooShort), findsOneWidget);
      expect(api.searches, isEmpty);
      await t.testTextInput.receiveAction(TextInputAction.search);
      await t.pump();
      expect(api.searches, isEmpty);
    });

    testWidgets('waits 600 ms after typing before searching', (t) async {
      final api = FakeProductsClient();
      await _pump(t, api, const SearchScreen());
      await t.enterText(find.byType(TextField), 'oats');
      await t.pump(const Duration(milliseconds: 500));
      expect(api.searches, isEmpty);
      await t.pump(const Duration(milliseconds: 150));
      await t.pumpAndSettle();
      expect(api.searches, ['oats']);
    });

    testWidgets('lists hits with their source; OFF hits are credited; a tap '
        'opens the result', (t) async {
      final api = FakeProductsClient()
        ..hits = const [
          SearchHit(
            attribution: null,
            barcode: null,
            brand: 'Ours',
            grade: NutriScoreGrade.c,
            name: 'Masala Oats',
            productId: 'p1',
            source: SearchHitSource.ours,
          ),
          SearchHit(
            attribution: 'attribution.off',
            barcode: '8901',
            brand: null,
            grade: null,
            name: 'Cola',
            productId: null,
            source: SearchHitSource.off,
          ),
        ];
      await _pump(t, api, const SearchScreen());
      await t.enterText(find.byType(TextField), '  oats ');
      await t.pump(const Duration(milliseconds: 600));
      await t.pumpAndSettle();
      expect(api.searches, ['oats']);
      expect(find.text('Masala Oats'), findsOneWidget);
      expect(find.text('Cola'), findsOneWidget);
      expect(find.text(en.searchSourceOurs), findsOneWidget);
      expect(find.text(en.searchSourceOff), findsOneWidget);
      expect(find.byType(OffAttribution), findsOneWidget);

      await t.tap(find.text('Cola'));
      await t.pumpAndSettle();
      expect(find.text('at /result?barcode=8901'), findsOneWidget);
    });

    testWidgets('no results', (t) async {
      final api = FakeProductsClient();
      await _pump(t, api, const SearchScreen());
      await t.enterText(find.byType(TextField), 'zzz');
      await t.pump(const Duration(milliseconds: 600));
      await t.pumpAndSettle();
      expect(find.text(en.searchNoResults), findsOneWidget);
    });

    testWidgets('error with retry', (t) async {
      final api = FakeProductsClient()..searchError = networkError();
      await _pump(t, api, const SearchScreen());
      await t.enterText(find.byType(TextField), 'oats');
      await t.pump(const Duration(milliseconds: 600));
      await t.pumpAndSettle();
      expect(find.text(en.errorNetwork), findsOneWidget);
      api.searchError = null;
      await t.tap(find.text(en.commonRetry));
      await t.pumpAndSettle();
      expect(find.text(en.searchNoResults), findsOneWidget);
    });

    testWidgets('picking the second product for a compare', (t) async {
      final api = FakeProductsClient()
        ..hits = const [
          SearchHit(
            attribution: null,
            barcode: null,
            brand: null,
            grade: NutriScoreGrade.b,
            name: 'Masala Oats',
            productId: 'p1',
            source: SearchHitSource.ours,
          ),
        ];
      await _pump(
        t,
        api,
        const SearchScreen(
          compareWith: (productId: null, barcode: '890'),
          memberId: 'm1',
        ),
      );
      expect(find.text(en.comparePickSecond), findsOneWidget);
      await t.enterText(find.byType(TextField), 'oats');
      await t.pump(const Duration(milliseconds: 600));
      await t.pumpAndSettle();
      await t.tap(find.text('Masala Oats'));
      await t.pumpAndSettle();
      expect(
        find.text('at /compare?a_barcode=890&b=p1&member_id=m1'),
        findsOneWidget,
      );
    });
  });

  group('CompareScreen', () {
    CompareOut out() => CompareOut(
      a: compareSide(
        name: 'Sugar Free Biscuit',
        productId: 'pa',
        grade: NutriScoreGrade.d,
        memberStatus: MemberStatus.avoid,
      ),
      b: compareSide(
        name: 'Oat Biscuit',
        barcode: '111',
        grade: NutriScoreGrade.a,
        per100g: nutrients(sugarsG: 5, fiberG: null),
        memberStatus: MemberStatus.unknown,
      ),
      better: const CompareBetter(
        energyKcal: BetterSide.same,
        fiberG: BetterSide.unknown,
        grade: BetterSide.b,
        proteinG: BetterSide.a,
        saltG: BetterSide.same,
        satFatG: BetterSide.$unknown,
        sugarsG: BetterSide.b,
      ),
    );

    testWidgets('renders both sides, the API better chips and the credits', (
      t,
    ) async {
      final api = FakeProductsClient()..compareOut = out();
      await _pump(
        t,
        api,
        const CompareScreen(
          a: (productId: 'pa', barcode: null),
          b: (productId: null, barcode: '111'),
          memberId: 'm1',
        ),
      );
      expect(api.compares.single, {
        'a': 'pa',
        'a_barcode': null,
        'b': null,
        'b_barcode': '111',
        'member_id': 'm1',
      });
      expect(find.text(en.compareTitle), findsOneWidget);
      expect(find.text('Sugar Free Biscuit'), findsOneWidget);
      expect(find.text('Oat Biscuit'), findsOneWidget);
      for (final row in [
        en.compareRowGrade,
        en.compareRowEnergyKcal,
        en.compareRowSugarsG,
        en.compareRowSaltG,
        en.compareRowSatFatG,
        en.compareRowProteinG,
        en.compareRowFiberG,
      ]) {
        await t.ensureVisible(find.text(row));
        expect(find.text(row), findsOneWidget);
      }
      // grade b, sugars b, protein a: three "Better" chips.
      expect(find.text(en.compareBetterChip), findsNWidgets(3));
      expect(find.byKey(const Key('compare-better-b-grade')), findsOneWidget);
      expect(
        find.byKey(const Key('compare-better-a-protein_g')),
        findsOneWidget,
      );
      expect(find.text(en.compareBetterSame), findsNWidgets(2));
      // fiber unknown, sat fat unrecognised: both "cannot compare".
      expect(find.text(en.compareBetterUnknown), findsNWidgets(2));
      // A missing value is never 0.
      expect(find.text(en.resultNotOnLabel), findsWidgets);

      final badges = t.widgetList<VerdictBadge>(find.byType(VerdictBadge));
      expect(badges.map((b) => b.status).toList(), ['avoid', 'unknown']);
      expect(find.text(en.commonDisclaimer), findsOneWidget);
      await t.ensureVisible(find.byType(OffAttribution));
      expect(find.byType(OffAttribution), findsOneWidget);
      // unknown member status is never green
      final unknownBadge = t.widget<Container>(
        find
            .descendant(
              of: find.byWidget(badges.last),
              matching: find.byType(Container),
            )
            .first,
      );
      expect(
        (unknownBadge.decoration! as BoxDecoration).color,
        SnColors.light.verdictUnknown,
      );
    });

    testWidgets('without a second product it offers the search', (t) async {
      final api = FakeProductsClient();
      await _pump(
        t,
        api,
        const CompareScreen(a: (productId: 'pa', barcode: null), b: null),
      );
      expect(api.compares, isEmpty);
      expect(find.text(en.comparePickSecond), findsOneWidget);
      await t.tap(find.text(en.comparePickSecond));
      await t.pumpAndSettle();
      expect(find.text('at /search?a=pa'), findsOneWidget);
    });

    testWidgets('error with retry', (t) async {
      final api = FakeProductsClient()..compareError = networkError();
      await _pump(
        t,
        api,
        const CompareScreen(
          a: (productId: 'pa', barcode: null),
          b: (productId: 'pb', barcode: null),
        ),
      );
      expect(find.text(en.errorNetwork), findsOneWidget);
      api
        ..compareError = null
        ..compareOut = out();
      await t.tap(find.text(en.commonRetry));
      await t.pumpAndSettle();
      expect(find.text('Oat Biscuit'), findsOneWidget);
    });
  });

  test('compare and search locations round-trip', () {
    final loc = compareLocation(
      (productId: 'pa', barcode: null),
      (productId: null, barcode: '890'),
      memberId: 'm1',
    );
    expect(loc, '/compare?a=pa&b_barcode=890&member_id=m1');
    final q = discoveryQuery(Uri.parse(loc).queryParameters);
    expect(q.a, (productId: 'pa', barcode: null));
    expect(q.b, (productId: null, barcode: '890'));
    expect(q.memberId, 'm1');
    expect(searchLocation(), '/search');
    expect(
      resultLocation((productId: null, barcode: '890')),
      '/result?barcode=890',
    );
    expect(
      resultLocation((productId: 'p', barcode: '890')),
      '/result?product_id=p',
    );
  });
}
