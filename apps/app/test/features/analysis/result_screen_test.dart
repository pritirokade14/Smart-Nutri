import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/analysis/data/analysis_repository.dart';
import 'package:smartnutri_ai/features/analysis/presentation/result_screen.dart';
import 'package:smartnutri_ai/features/analysis/presentation/verdict_card.dart';
import 'package:smartnutri_ai/shared/widgets/off_attribution.dart';
import 'package:smartnutri_api/src/export.dart';

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
}

Widget _app(
  AnalysisRepository repo, {
  String locale = 'en',
  String barcode = '8901063201089',
  List<Uri>? opened,
}) => ProviderScope(
  overrides: [
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
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    pending.complete(analyzeFixture('water'));
    await t.pumpAndSettle();
    expect(find.byType(CircularProgressIndicator), findsNothing);
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
      for (final v in body.verdicts) t.getTopLeft(find.text(v.memberName)).dy,
    ];
    expect(ys, [...ys]..sort(), reason: 'cards keep the API order');
    final cards = t.widgetList<VerdictCard>(find.byType(VerdictCard)).toList();
    expect(
      cards.map((c) => c.verdict.memberId).toList(),
      body.verdicts.map((v) => v.memberId).toList(),
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
}
