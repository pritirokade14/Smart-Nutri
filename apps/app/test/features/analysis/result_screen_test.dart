import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/features/product/data/product_discovery_repository.dart';
import 'package:smartnutri_ai/features/reports/presentation/report_dialog.dart';
import 'package:smartnutri_ai/shared/share/share_sheet.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_ai/shared/widgets/states.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_products.dart';
import '../../support/test_config.dart';
import '../../support/fixtures.dart';

class FakeAnalysisRepository implements AnalysisRepository {
  FakeAnalysisRepository(this.responses);

  /// One response per call; the last one repeats.
  final List<FutureOr<AnalyzeOut> Function()> responses;
  final calls = <(String, String)>[];

  @override
  Future<AnalyzeOut> analyzeBarcode(
    String barcode, {
    String language = 'en',
  }) async {
    calls.add((barcode, language));
    final i = calls.length - 1;
    return responses[i < responses.length ? i : responses.length - 1]();
  }

  @override
  Future<AnalyzeOut> analyzeProduct(
    String productId, {
    String language = 'en',
  }) async {
    calls.add(('product:$productId', language));
    final i = calls.length - 1;
    return responses[i < responses.length ? i : responses.length - 1]();
  }
}

Widget _app(
  AnalysisRepository repo, {
  String locale = 'en',
  String barcode = '8901063201089',
  List<Uri>? opened,
  FakeMealsClient? meals,
  FakeProductsClient? products,
  List<String>? shared,
  String siteUrl = testSiteUrl,
}) => ProviderScope(
  overrides: [
    testConfigOverride(siteUrl: siteUrl),
    shareLauncherProvider.overrideWithValue((text) async => shared?.add(text)),
    ...mealTestOverrides(client: meals ?? FakeMealsClient()),
    productDiscoveryRepositoryProvider.overrideWithValue(
      ProductDiscoveryRepository(products ?? FakeProductsClient()),
    ),
    analysisRepositoryProvider.overrideWithValue(repo),
    openExternalUrlProvider.overrideWithValue((uri) async {
      opened?.add(uri);
      return true;
    }),
  ],
  child: MaterialApp(
    locale: Locale(locale),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: ResultScreen(barcode: barcode),
  ),
);

AnalyzeOut _offProduct() {
  final json = analyzeJson('namkeen');
  final product = Map<String, Object?>.from(json['product']! as Map)
    ..['source'] = 'openfoodfacts'
    ..['attribution'] = 'Open Food Facts contributors, ODbL'
    ..['barcode'] = '8901063201089'
    ..['product_id'] = null;
  json['product'] = product;
  return AnalyzeOut.fromJson(json);
}

final en = lookupAppLocalizations(const Locale('en'));

void main() {
  testWidgets('loading state while the API answers', (t) async {
    final pending = Completer<AnalyzeOut>();
    await t.pumpWidget(_app(FakeAnalysisRepository([() => pending.future])));
    expect(find.byType(LoadingSkeleton), findsOneWidget);
    pending.complete(analyzeFixture('water'));
    await t.pumpAndSettle();
    expect(find.byType(LoadingSkeleton), findsNothing);
  });

  testWidgets('renders product, grade, high-in and one card per verdict in API '
      'order', (t) async {
    final body = analyzeFixture('sf_biscuit');
    final repo = FakeAnalysisRepository([() => body]);
    await t.pumpWidget(_app(repo));
    await t.pumpAndSettle();

    expect(repo.calls.single, ('8901063201089', 'en'));
    expect(find.text('Sugar Free Biscuit'), findsOneWidget);
    expect(find.byKey(const Key('nutriscore-grade-tile')), findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const Key('nutriscore-grade-tile')),
        matching: find.text('D'),
      ),
      findsOneWidget,
    );
    expect(find.text(en.nutriscoreCalculatedBy), findsOneWidget);
    expect(find.text(en.resultHighInTitle), findsOneWidget);
    expect(find.text(en.highInSatFat), findsOneWidget);

    expect(find.byType(VerdictCard), findsNWidgets(body.verdicts.length));
    final ys = [
      for (final v in body.verdicts)
        t.getTopLeft(find.text(verdictHeadline(en, v))).dy,
    ];
    expect(ys, [...ys]..sort(), reason: 'cards keep the API order');
    final cards = t.widgetList<VerdictCard>(find.byType(VerdictCard)).toList();
    expect(
      cards.map((c) => c.verdict.memberId).toList(),
      body.verdicts.map((v) => v.memberId).toList(),
    );
  });

  testWidgets('explanation card hidden when unavailable', (t) async {
    final body = analyzeFixture('sf_biscuit');
    expect(body.explanation.source, ExplanationOutSource.unavailable);
    await t.pumpWidget(_app(FakeAnalysisRepository([() => body])));
    await t.pumpAndSettle();
    expect(find.text(en.explanationTitle), findsNothing);
    expect(find.text(en.commonDisclaimer), findsOneWidget);
  });

  testWidgets('explanation card under the verdicts, names substituted, '
      'disclaimer below it', (t) async {
    final json = analyzeJson('sf_biscuit');
    final first = (json['verdicts']! as List).first as Map;
    json['explanation'] = {
      'language': 'en',
      'member_refs': {'member_1': first['member_id']},
      'prompt_version': 'explanation_v1',
      'source': 'llm',
      'text': 'Sugar matters for member_1.',
      'tips': ['Check the serving size.'],
    };
    final body = AnalyzeOut.fromJson(json);
    await t.pumpWidget(_app(FakeAnalysisRepository([() => body])));
    await t.pumpAndSettle();
    final text = 'Sugar matters for ${first['member_name']}.';
    await t.scrollUntilVisible(find.text(text), 300);
    expect(find.text(en.explanationTitle), findsOneWidget);
    expect(find.text(en.explanationAiNote), findsOneWidget);
    expect(find.text('Check the serving size.'), findsOneWidget);
    final lastCard = find.byType(VerdictCard).last;
    expect(
      t.getTopLeft(find.text(text)).dy,
      greaterThan(t.getTopLeft(lastCard).dy),
    );
    await t.scrollUntilVisible(find.text(en.commonDisclaimer), 300);
    expect(
      t.getTopLeft(find.text(en.commonDisclaimer)).dy,
      greaterThan(t.getTopLeft(find.text(text)).dy),
    );
  });

  testWidgets('disclaimer always shown on result', (t) async {
    for (final product in fixtureProducts()) {
      await t.pumpWidget(
        _app(FakeAnalysisRepository([() => analyzeFixture(product)])),
      );
      await t.pumpAndSettle();
      expect(find.text(en.commonDisclaimer), findsOneWidget, reason: product);
      await t.pumpWidget(const SizedBox());
    }
  });

  testWidgets('OFF attribution hidden for our own catalogue products', (
    t,
  ) async {
    for (final product in fixtureProducts()) {
      final body = analyzeFixture(product);
      expect(body.product.source, ProductOutSource.smartnutri);
      await t.pumpWidget(_app(FakeAnalysisRepository([() => body])));
      await t.pumpAndSettle();
      expect(find.byType(OffAttribution), findsNothing, reason: product);
      expect(find.text(en.attributionOff), findsNothing);
      await t.pumpWidget(const SizedBox());
    }
  });

  testWidgets('OFF attribution shown for openfoodfacts source and links to '
      'the OFF product page', (t) async {
    final opened = <Uri>[];
    await t.pumpWidget(
      _app(FakeAnalysisRepository([_offProduct]), opened: opened),
    );
    await t.pumpAndSettle();
    expect(find.byType(OffAttribution), findsOneWidget);
    expect(find.text(en.attributionOff), findsOneWidget);
    await t.ensureVisible(find.text(en.attributionOff));
    await t.tap(find.text(en.attributionOff));
    await t.pump();
    expect(opened, [
      Uri.parse('https://world.openfoodfacts.org/product/8901063201089'),
    ]);
  });

  testWidgets('report a problem opens the dialog for our own products', (
    t,
  ) async {
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => analyzeFixture('namkeen')])),
    );
    await t.pumpAndSettle();
    await t.ensureVisible(find.byKey(ResultScreen.reportKey));
    await t.tap(find.byKey(ResultScreen.reportKey));
    await t.pumpAndSettle();
    final dialog = t.widget<ReportDialog>(find.byType(ReportDialog));
    expect(dialog.productId, analyzeFixture('namkeen').product.productId);
  });

  testWidgets('no report button for Open Food Facts products (no product_id)', (
    t,
  ) async {
    await t.pumpWidget(_app(FakeAnalysisRepository([_offProduct])));
    await t.pumpAndSettle();
    expect(find.byKey(ResultScreen.reportKey), findsNothing);
  });

  testWidgets('how we score link is on the result', (t) async {
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => analyzeFixture('water')])),
    );
    await t.pumpAndSettle();
    expect(find.byKey(ResultScreen.methodologyKey), findsOneWidget);
    expect(find.text(en.methodologyTitle), findsOneWidget);
  });

  testWidgets('no grade shows insufficient-data text', (t) async {
    final json = analyzeJson('water');
    final report = Map<String, Object?>.from(json['report']! as Map);
    report['nutriscore'] = {
      'approximated': false,
      'grade': null,
      'partial': true,
      'points': null,
      'reason': 'insufficient_data',
    };
    json['report'] = report;
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => AnalyzeOut.fromJson(json)])),
    );
    await t.pumpAndSettle();
    expect(find.text(en.nutriscoreInsufficientData), findsOneWidget);
    expect(find.textContaining('Nutri-Score A'), findsNothing);
  });

  testWidgets('404 shows not-found with retry; retry calls the API again', (
    t,
  ) async {
    final repo = FakeAnalysisRepository([
      () => throw const AnalysisNotFound(),
      () => analyzeFixture('curd'),
    ]);
    await t.pumpWidget(_app(repo));
    await t.pumpAndSettle();
    expect(find.text(en.scanNotFound), findsOneWidget);
    expect(find.byType(VerdictCard), findsNothing);
    await t.tap(find.text(en.scanRetry));
    await t.pumpAndSettle();
    expect(repo.calls.length, 2);
    expect(find.text('Curd'), findsOneWidget);
    expect(find.text(en.commonDisclaimer), findsOneWidget);
  });

  testWidgets('503 shows off-unavailable with retry', (t) async {
    final repo = FakeAnalysisRepository([
      () => throw const AnalysisUnavailable(),
    ]);
    await t.pumpWidget(_app(repo));
    await t.pumpAndSettle();
    expect(find.text(en.scanOffUnavailable), findsOneWidget);
    await t.tap(find.text(en.scanRetry));
    await t.pumpAndSettle();
    expect(repo.calls.length, 2);
    expect(find.text(en.scanOffUnavailable), findsOneWidget);
  });

  testWidgets('invalid barcode, network and other errors are localized', (
    t,
  ) async {
    Future<void> check(Object failure, String text) async {
      await t.pumpWidget(_app(FakeAnalysisRepository([() => throw failure])));
      await t.pumpAndSettle();
      expect(find.text(text), findsOneWidget);
      expect(find.text(en.scanRetry), findsOneWidget);
      await t.pumpWidget(const SizedBox());
    }

    await check(const AnalysisNetworkFailure(), en.errorNetwork);
    final ro = RequestOptions(path: '/v1/analyze');
    await check(
      AnalysisApiFailure(
        DioException(
          requestOptions: ro,
          response: Response<Object?>(
            requestOptions: ro,
            statusCode: 429,
            data: {
              'error': {
                'code': 'rate_limited',
                'message_key': 'error.rate_limited',
                'details': <String, Object?>{},
              },
            },
          ),
        ),
      ),
      en.errorRateLimited,
    );
  });

  testWidgets('API invalid-barcode error has no retry button', (t) async {
    await t.pumpWidget(
      _app(
        FakeAnalysisRepository([() => throw const AnalysisInvalidBarcode()]),
      ),
    );
    await t.pumpAndSettle();
    expect(find.text(en.errorInvalidBarcode), findsOneWidget);
    expect(find.text(en.scanRetry), findsNothing);
  });

  testWidgets('invalid deep-link barcode: error, no API call, no retry', (
    t,
  ) async {
    final repo = FakeAnalysisRepository([() => analyzeFixture('water')]);
    await t.pumpWidget(_app(repo, barcode: '123'));
    await t.pumpAndSettle();
    expect(find.text(en.errorInvalidBarcode), findsOneWidget);
    expect(find.text(en.scanRetry), findsNothing);
    expect(repo.calls, isEmpty);
  });

  testWidgets('deep-link barcode is normalised before the API call', (t) async {
    final repo = FakeAnalysisRepository([() => analyzeFixture('water')]);
    await t.pumpWidget(_app(repo, barcode: '8901-0632 01089'));
    await t.pumpAndSettle();
    expect(repo.calls.single.$1, '8901063201089');
  });

  testWidgets('requests the analysis in the UI language', (t) async {
    final repo = FakeAnalysisRepository([() => analyzeFixture('oats')]);
    await t.pumpWidget(_app(repo, locale: 'mr'));
    await t.pumpAndSettle();
    expect(repo.calls.single.$2, 'mr');
    final mr = lookupAppLocalizations(const Locale('mr'));
    expect(find.text(mr.commonDisclaimer), findsOneWidget);
  });

  testWidgets('each member card has "I ate this"; it logs for that member', (
    t,
  ) async {
    final body = analyzeFixture('sf_biscuit');
    final meals = FakeMealsClient();
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => body]), meals: meals),
    );
    await t.pumpAndSettle();
    expect(find.text(en.mealsLogCta), findsNWidgets(body.verdicts.length));

    final target = body.verdicts[4];
    final button = find.byKey(Key('i-ate-this-${target.memberId}'));
    await t.ensureVisible(button);
    await t.pumpAndSettle();
    await t.tap(button);
    await t.pumpAndSettle();
    final save = find.byKey(const Key('log-meal-save'));
    await t.ensureVisible(save);
    await t.pumpAndSettle();
    await t.tap(save);
    await t.pumpAndSettle();

    final sent = meals.logged.single;
    expect(sent.memberId, target.memberId);
    expect(sent.productId, body.product.productId);
    expect(sent.barcode, isNull);
    expect(sent.servings, 1, reason: 'the product has a serving size');
    expect(find.text(en.mealsLogSaved(target.memberName)), findsOneWidget);

    await t.tap(find.text(en.mealsLogUndo));
    await t.pumpAndSettle();
    expect(meals.deleted, ['meal-1']);
  });

  testWidgets('an OFF product is logged by barcode', (t) async {
    final meals = FakeMealsClient();
    await t.pumpWidget(
      _app(FakeAnalysisRepository([_offProduct]), meals: meals),
    );
    await t.pumpAndSettle();
    final button = find.text(en.mealsLogCta).first;
    await t.ensureVisible(button);
    await t.pumpAndSettle();
    await t.tap(button);
    await t.pumpAndSettle();
    final save = find.byKey(const Key('log-meal-save'));
    await t.ensureVisible(save);
    await t.pumpAndSettle();
    await t.tap(save);
    await t.pumpAndSettle();
    expect(meals.logged.single.barcode, '8901063201089');
    expect(meals.logged.single.productId, isNull);
  });

  testWidgets('share: product and grade by default, every member unticked '
      '(ruling SH1)', (t) async {
    final body = analyzeFixture('sf_biscuit');
    final shared = <String>[];
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => body]), shared: shared),
    );
    await t.pumpAndSettle();
    final button = find.widgetWithText(OutlinedButton, en.shareButton);
    await t.ensureVisible(button);
    await t.pumpAndSettle();
    await t.tap(button);
    await t.pumpAndSettle();
    final tiles = t
        .widgetList<CheckboxListTile>(find.byType(CheckboxListTile))
        .toList();
    expect(tiles, hasLength(body.verdicts.length));
    expect(tiles.every((c) => c.value == false), isTrue);
    final send = find.byKey(ShareSheet.shareKey);
    await t.ensureVisible(send);
    await t.tap(send);
    await t.pumpAndSettle();
    expect(shared, [
      'Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). '
          'Checked with SmartNutri: https://site.example/en',
    ]);
  });

  testWidgets('share without SITE_URL: no link and no Copy link (ruling SH1)', (
    t,
  ) async {
    final body = analyzeFixture('sf_biscuit');
    final shared = <String>[];
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => body]), shared: shared, siteUrl: ''),
    );
    await t.pumpAndSettle();
    final button = find.widgetWithText(OutlinedButton, en.shareButton);
    await t.ensureVisible(button);
    await t.pumpAndSettle();
    await t.tap(button);
    await t.pumpAndSettle();
    expect(find.text(en.shareCopyLink), findsNothing);
    final send = find.byKey(ShareSheet.shareKey);
    await t.ensureVisible(send);
    await t.tap(send);
    await t.pumpAndSettle();
    expect(shared, [
      'Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri).',
    ]);
  });

  testWidgets('share: privacy note, the members the user ticks, no health '
      'data', (t) async {
    final body = analyzeFixture('sf_biscuit');
    final shared = <String>[];
    await t.pumpWidget(
      _app(FakeAnalysisRepository([() => body]), shared: shared),
    );
    await t.pumpAndSettle();
    final button = find.widgetWithText(OutlinedButton, en.shareButton);
    await t.ensureVisible(button);
    await t.pumpAndSettle();
    await t.tap(button);
    await t.pumpAndSettle();
    expect(find.text(en.sharePrivacyNote), findsOneWidget);
    expect(find.byType(CheckboxListTile), findsNWidgets(body.verdicts.length));

    // Tick only the first member.
    final firstTile = find.byType(CheckboxListTile).first;
    await t.ensureVisible(firstTile);
    await t.tap(firstTile);
    await t.pumpAndSettle();
    final send = find.byKey(ShareSheet.shareKey);
    await t.ensureVisible(send);
    await t.tap(send);
    await t.pumpAndSettle();
    final first = body.verdicts.first;
    expect(shared, [
      'Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). '
          '${first.memberName.split(' ').first}: ${en.verdictStatusCaution}. '
          'Checked with SmartNutri: https://site.example/en',
    ]);
    expect(first.status, VerdictOutStatus.caution);
  });
}
