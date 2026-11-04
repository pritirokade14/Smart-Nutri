import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/domain/report.dart';
import 'package:smartnutri_ai/features/analysis/presentation/protein_facts.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/members/presentation/member_form_screen.dart';
import 'package:smartnutri_ai/features/product/data/product_discovery_repository.dart';
import 'package:smartnutri_ai/features/product/presentation/alternatives_section.dart';
import 'package:smartnutri_ai/features/product/presentation/compare_screen.dart';
import 'package:smartnutri_ai/features/product/presentation/search_screen.dart';
import 'package:smartnutri_ai/features/protein/domain/price_per_scoop.dart';
import 'package:smartnutri_ai/features/protein/presentation/price_per_scoop_section.dart';
import 'package:smartnutri_ai/features/protein/presentation/protein_screen.dart';
import 'package:smartnutri_ai/features/protein/presentation/protein_swaps.dart';
import 'package:smartnutri_ai/shared/widgets/nutri_score_chip.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_members.dart';
import '../../support/fake_products.dart';
import '../../support/fake_user_types.dart';
import '../../support/fixtures.dart';
import '../user_types/user_types_harness.dart';

class _Analysis implements AnalysisRepository {
  _Analysis(this.out);
  final AnalyzeOut out;

  @override
  Future<AnalyzeOut> analyzeBarcode(
    String barcode, {
    String language = 'en',
  }) async => out;

  @override
  Future<AnalyzeOut> analyzeProduct(
    String productId, {
    String language = 'en',
  }) async => out;
}

MemberOut _primary({int birthYear = 1990}) => memberOut(
  id: 'p1',
  name: 'Ravi',
  relation: MemberOutRelation.self,
  birthYear: birthYear,
  diet: MemberOutDiet.nonVeg,
  isPrimary: true,
);

Future<AppHarness> _pump(
  WidgetTester t, {
  FakeProductsClient? products,
  AnalyzeOut? analysis,
  FakeMealsClient? meals,
  FakeMembersClient? members,
  String mode = 'gym',
}) => pumpApp(
  t,
  FakeUserTypesApi(
    me: FakeUserTypesMe(userTypesOut(types: [mode])),
    members: members ?? FakeMembersClient([_primary()]),
    consents: FakeConsentsClient(granted: {'terms', 'health_data'}),
  ),
  meals: meals,
  overrides: [
    productDiscoveryRepositoryProvider.overrideWithValue(
      ProductDiscoveryRepository(products ?? FakeProductsClient()),
    ),
    if (analysis != null)
      analysisRepositoryProvider.overrideWithValue(_Analysis(analysis)),
  ],
);

Future<void> _tapKey(WidgetTester t, Key key) async {
  await t.ensureVisible(find.byKey(key));
  await t.pumpAndSettle();
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

CompareOut _compareOut() => CompareOut(
  a: compareSide(name: 'Whey A', productId: 'pa'),
  b: CompareSide(
    attribution: null,
    barcode: null,
    brand: null,
    grade: null,
    highIn: const [],
    memberStatus: null,
    name: 'Whey B',
    per100g: nutrients(),
    productId: 'pb',
    proteinPer100kcal: 19.5,
    proteinPerServingG: 24,
    servingSizeG: 33,
    sugarsPerServingG: null,
  ),
  better: const CompareBetter(
    energyKcal: BetterSide.same,
    fiberG: BetterSide.unknown,
    grade: BetterSide.unknown,
    proteinG: BetterSide.same,
    saltG: BetterSide.same,
    satFatG: BetterSide.same,
    sugarsG: BetterSide.same,
    proteinPer100kcal: BetterSide.b,
    proteinPerServingG: BetterSide.b,
    sugarsPerServingG: BetterSide.unknown,
  ),
);

void main() {
  test('price per scoop matches shared fixture', () {
    final f =
        jsonDecode(
              File(
                '../../packages/test-fixtures/protein/price_per_scoop.json',
              ).readAsStringSync(),
            )
            as Map<String, Object?>;
    for (final c in (f['cases']! as List).cast<Map<String, Object?>>()) {
      expect(
        pricePerScoop(
          c['price'] as num?,
          c['pack_size_g'] as num?,
          c['serving_size_g'] as num?,
        ),
        c['expected'],
        reason: c['name'] as String,
      );
    }
  });

  testWidgets('protein facts row shows dash for null', (t) async {
    await t.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: const Scaffold(
          body: ProteinFactsRow(
            facts: (perServing: null, per100g: 12.5, per100kcal: null),
          ),
        ),
      ),
    );
    await t.pumpAndSettle();
    final serving = t.widget<Text>(
      find.byKey(ProteinFactsRow.valueKey('serving')),
    );
    expect(serving.data, ProteinFactsRow.dash);
    expect(serving.data, isNot('0'));
    expect(
      t.widget<Text>(find.byKey(ProteinFactsRow.valueKey('100g'))).data,
      '12.5',
    );
    expect(
      t.widget<Text>(find.byKey(ProteinFactsRow.valueKey('100kcal'))).data,
      ProteinFactsRow.dash,
    );
  });

  testWidgets('supplement shows not graded label', (t) async {
    final whey = analyzeFixture('whey_powder');
    expect(nutriscoreReason(whey.report), 'not_scored_supplement');
    final h = await _pump(t, analysis: whey);
    h.router.push('/result?product_id=whey');
    await t.pumpAndSettle();
    expect(find.byType(ResultScreen), findsOneWidget);
    expect(find.text(en.nutriscoreNotScoredSupplement), findsOneWidget);
    expect(find.byKey(NutriScoreChip.gradeTileKey), findsNothing);
    // The facts from the report, and the sweetener as information.
    expect(
      t.widget<Text>(find.byKey(ProteinFactsRow.valueKey('serving'))).data,
      '24',
    );
    expect(find.text('${en.reportSweeteners}: sucralose'), findsOneWidget);
    // New claim results in the claims section.
    expect(find.textContaining(en.claimWheyOnly), findsWidgets);
  });

  testWidgets('higher protein toggle requests sort=protein with member', (
    t,
  ) async {
    final products = FakeProductsClient();
    final h = await _pump(
      t,
      products: products,
      analysis: analyzeFixture('curd'),
    );
    h.router.push('/result?product_id=curd');
    await t.pumpAndSettle();
    expect(products.alternativesSorts.last, AlternativesSort.grade);
    await _tapKey(t, AlternativesSection.proteinSortKey);
    expect(products.alternativesSorts.last, AlternativesSort.protein);
    expect(products.alternativesCalls.last.$3, isNotNull);
  });

  testWidgets('search protein sort', (t) async {
    final products = FakeProductsClient();
    final h = await _pump(t, products: products);
    h.router.push('/search');
    await t.pumpAndSettle();
    await t.enterText(find.byType(TextField).first, 'whey');
    await t.testTextInput.receiveAction(TextInputAction.search);
    await t.pumpAndSettle();
    expect(products.searchCalls.last.sort, SearchSort.relevance);
    await _tapKey(t, SearchScreen.proteinSortKey);
    expect(products.searchCalls.last.sort, SearchSort.protein);
    expect(products.searchCalls.last.q, 'whey');
  });

  testWidgets('protein screen lists swaps for logged items', (t) async {
    final products = FakeProductsClient()
      ..alternativesOut = AlternativesOut(
        items: [
          alternative(name: 'Paneer Bar', productId: 'x1'),
          alternative(
            name: 'Avoid Bar',
            productId: 'x2',
            memberStatus: MemberStatus.avoid,
          ),
        ],
        reason: AlternativesOutReason.ok,
      );
    final meals = FakeMealsClient()
      ..meals = [
        mealOut(
          id: 'meal-1',
          memberId: 'p1',
          productName: 'Glucose Biscuit',
          eatenAt: DateTime.now().toUtc(),
        ),
      ]
      ..summary = (id, _) => null;
    final h = await _pump(t, products: products, meals: meals);
    h.router.go('/protein');
    await t.pumpAndSettle();
    expect(find.byType(ProteinScreen), findsOneWidget);
    expect(find.text('Glucose Biscuit'), findsOneWidget);
    await _tapKey(t, ProteinSwaps.optionsKey('meal-1'));
    expect(products.alternativesSorts.last, AlternativesSort.protein);
    expect(products.alternativesCalls.last, ('p1', null, 'p1'));
    expect(find.text('Paneer Bar'), findsOneWidget);
    expect(find.text('Avoid Bar'), findsNothing);
    // The protein-ranked search for the member.
    await t.ensureVisible(find.byKey(ProteinSwaps.searchKey));
    await t.enterText(find.byKey(ProteinSwaps.searchKey), 'paneer');
    await t.testTextInput.receiveAction(TextInputAction.search);
    await t.pumpAndSettle();
    expect(products.searchCalls.last, (
      q: 'paneer',
      sort: SearchSort.protein,
      memberId: 'p1',
    ));
  });

  testWidgets('compare shows protein rows and markers', (t) async {
    final products = FakeProductsClient()..compareOut = _compareOut();
    final h = await _pump(t, products: products);
    h.router.push('/compare?a=pa&b=pb');
    await t.pumpAndSettle();
    expect(find.text(en.proteinCompareProteinServing), findsOneWidget);
    expect(find.text(en.proteinCompareProtein100kcal), findsOneWidget);
    expect(find.text(en.proteinCompareSugar), findsOneWidget);
    expect(
      find.byKey(const Key('compare-better-b-protein_per_100kcal')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('compare-better-b-protein_per_serving_g')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('compare-better-a-protein_per_100kcal')),
      findsNothing,
    );
  });

  testWidgets('price is never persisted or sent', (t) async {
    final products = FakeProductsClient()..compareOut = _compareOut();
    final meals = FakeMealsClient();
    final h = await _pump(t, products: products, meals: meals);
    h.router.push('/compare?a=pa&b=pb');
    await t.pumpAndSettle();
    final compares = products.compares.length;
    final events = [...h.events];
    await t.ensureVisible(find.byKey(PricePerScoopSection.priceKey('b')));
    await t.enterText(find.byKey(PricePerScoopSection.priceKey('b')), '2499');
    await t.enterText(find.byKey(PricePerScoopSection.packKey('b')), '1000');
    await t.pumpAndSettle();
    expect(
      t.widget<Text>(find.byKey(PricePerScoopSection.resultKey('b'))).data,
      contains('82.47'),
    );
    // Side a has no serving size: no price per scoop.
    await t.enterText(find.byKey(PricePerScoopSection.priceKey('a')), '999');
    await t.enterText(find.byKey(PricePerScoopSection.packKey('a')), '500');
    await t.pumpAndSettle();
    expect(
      t.widget<Text>(find.byKey(PricePerScoopSection.resultKey('a'))).data,
      '—',
    );
    expect(products.compares, hasLength(compares), reason: 'no new request');
    expect(products.searches, isEmpty);
    expect(meals.logged, isEmpty);
    expect(h.events, events, reason: 'no analytics');
    expect(
      h.router.routerDelegate.currentConfiguration.uri.toString(),
      isNot(contains('2499')),
    );
    // Leaving and reopening the screen forgets the price.
    h.router.pop();
    await t.pumpAndSettle();
    h.router.push('/compare?a=pa&b=pb');
    await t.pumpAndSettle();
    await t.ensureVisible(find.byKey(PricePerScoopSection.priceKey('b')));
    expect(
      t
          .widget<TextField>(find.byKey(PricePerScoopSection.priceKey('b')))
          .controller!
          .text,
      isEmpty,
    );
  });

  testWidgets('compare without products shows the pick state', (t) async {
    final h = await _pump(t);
    h.router.push('/compare');
    await t.pumpAndSettle();
    expect(find.byType(CompareScreen), findsOneWidget);
    expect(find.byKey(CompareScreen.pickKey), findsOneWidget);
    expect(find.text(en.errorInvalidProductRef), findsNothing);
  });

  testWidgets('member form offers build muscle', (t) async {
    final members = FakeMembersClient([
      _primary(),
      memberOut(id: 'k1', name: 'Asha', birthYear: 2015),
    ]);
    final h = await _pump(t, members: members);
    h.router.go('/family/p1');
    await t.pumpAndSettle();
    expect(find.byType(MemberFormScreen), findsOneWidget);
    expect(find.text(en.membersGoalBuildMuscle), findsOneWidget);
    await t.ensureVisible(find.text(en.membersGoalBuildMuscle));
    await t.tap(find.text(en.membersGoalBuildMuscle));
    await t.pumpAndSettle();
    await _tapKey(t, MemberFormScreen.saveKey);
    expect(members.patched.single.$2.goal?.json, 'build_muscle');
    // A child is not offered the goal.
    h.router.go('/family/k1');
    await t.pumpAndSettle();
    expect(find.text(en.membersGoalBuildMuscle), findsNothing);
  });

  testWidgets('a 422 for build muscle shows the error and saves nothing', (
    t,
  ) async {
    final members = FakeMembersClient([_primary()])
      ..error = apiError(
        422,
        'validation_error',
        details: {
          'fields': ['body.goal'],
        },
      );
    final h = await _pump(t, members: members);
    h.router.go('/family/p1');
    await t.pumpAndSettle();
    await t.ensureVisible(find.text(en.membersGoalBuildMuscle));
    await t.tap(find.text(en.membersGoalBuildMuscle));
    await t.pumpAndSettle();
    await _tapKey(t, MemberFormScreen.saveKey);
    // The API's minor rejection (422 body.goal) is shown on the goal field.
    expect(find.byKey(MemberFormScreen.goalErrorKey), findsOneWidget);
    expect(find.text(en.membersGoalBuildMuscleAdultsOnly), findsOneWidget);
    expect(find.text(en.errorValidationError), findsNothing);
    expect(find.byType(MemberFormScreen), findsOneWidget);
    // Picking another goal clears it.
    await t.tap(find.text(en.membersGoalHealthyEating));
    await t.pumpAndSettle();
    expect(find.byKey(MemberFormScreen.goalErrorKey), findsNothing);
  });

  testWidgets('another 422 keeps the generic error', (t) async {
    final members = FakeMembersClient([_primary()])
      ..error = apiError(422, 'validation_error');
    final h = await _pump(t, members: members);
    h.router.go('/family/p1');
    await t.pumpAndSettle();
    await t.ensureVisible(find.text(en.membersGoalBuildMuscle));
    await t.tap(find.text(en.membersGoalBuildMuscle));
    await t.pumpAndSettle();
    await _tapKey(t, MemberFormScreen.saveKey);
    expect(find.text(en.errorValidationError), findsOneWidget);
    expect(find.byKey(MemberFormScreen.goalErrorKey), findsNothing);
  });
}
