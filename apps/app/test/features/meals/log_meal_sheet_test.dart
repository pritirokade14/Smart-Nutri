import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';
import 'package:smartnutri_ai/features/meals/presentation/log_meal_sheet.dart';

import '../../support/fake_meals.dart';
import '../../support/fixtures.dart';

final en = lookupAppLocalizations(const Locale('en'));

class _Harness {
  final client = FakeMealsClient();
  final queue = MemoryMealQueue();
  MealLogResult? result;
  bool closed = false;
}

Future<_Harness> _open(
  WidgetTester t, {
  num? servingSizeG,
  String? productId = 'p1',
  String? barcode,
  List<Object>? responses,
}) async {
  final h = _Harness();
  h.client.logResponses.addAll(responses ?? const []);
  final verdicts = analyzeFixture('sf_biscuit').verdicts;
  final product = LogMealProduct(
    productId: productId,
    barcode: barcode,
    name: 'Sugar Free Biscuit',
    servingSizeG: servingSizeG,
  );
  await t.pumpWidget(
    ProviderScope(
      overrides: mealTestOverrides(queue: h.queue, client: h.client),
      child: MaterialApp(
        locale: const Locale('en'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) => Scaffold(
            body: Center(
              child: TextButton(
                onPressed: () async {
                  h.result = await showLogMealSheet(
                    context,
                    product: product,
                    verdicts: verdicts,
                    memberId: verdicts[1].memberId,
                  );
                  h.closed = true;
                },
                child: const Text('open'),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await t.tap(find.text('open'));
  await t.pumpAndSettle();
  return h;
}

Finder _save() => find.byKey(LogMealSheet.saveKey);

Future<void> _tapSave(WidgetTester t) async {
  await t.ensureVisible(_save());
  await t.pumpAndSettle();
  await t.tap(_save());
  await t.pumpAndSettle();
}

void main() {
  testWidgets('servings hidden without serving size', (t) async {
    await _open(t, servingSizeG: null);
    expect(find.text(en.mealsLogTitle), findsOneWidget);
    expect(find.text(en.mealsLogServings), findsNothing);
    expect(find.text(en.mealsLogAmountGrams), findsOneWidget);
    // No portion yet: save stays disabled.
    expect(t.widget<FilledButton>(_save()).onPressed, isNull);
  });

  testWidgets('with a serving size, servings default to 1 and are sent', (
    t,
  ) async {
    final h = await _open(t, servingSizeG: 25);
    expect(find.text(en.mealsLogServings), findsOneWidget);
    expect(find.text(en.mealsLogGrams), findsOneWidget);
    expect(find.text(en.mealsLogServingSize('25')), findsOneWidget);
    expect(
      t.widget<TextField>(find.byKey(LogMealSheet.amountKey)).controller?.text,
      '1',
    );
    await _tapSave(t);
    final body = h.client.logged.single;
    expect(body.servings, 1);
    expect(body.grams, isNull);
    expect(body.productId, 'p1');
    expect(body.memberId, analyzeFixture('sf_biscuit').verdicts[1].memberId);
    expect(body.eatenAt?.isUtc, isTrue);
    expect(h.result, isA<MealLogged>());
    expect(h.queue.rows, isEmpty);
  });

  testWidgets('grams: typed amount is sent; bad input keeps save disabled', (
    t,
  ) async {
    final h = await _open(t, servingSizeG: 25, productId: null, barcode: '1');
    await t.tap(find.text(en.mealsLogGrams));
    await t.pumpAndSettle();
    final field = find.byKey(LogMealSheet.amountKey);
    await t.enterText(field, '0');
    await t.pump();
    expect(t.widget<FilledButton>(_save()).onPressed, isNull);
    await t.enterText(field, 'abc');
    await t.pump();
    expect(t.widget<FilledButton>(_save()).onPressed, isNull);
    await t.enterText(field, '5001');
    await t.pump();
    expect(t.widget<FilledButton>(_save()).onPressed, isNull);
    await t.enterText(field, '45.5');
    await t.pump();
    await _tapSave(t);
    final body = h.client.logged.single;
    expect(body.grams, 45.5);
    expect(body.servings, isNull);
    expect(body.barcode, '1');
    expect(body.productId, isNull);
  });

  testWidgets('the member can be changed', (t) async {
    final h = await _open(t, servingSizeG: 25);
    final verdicts = analyzeFixture('sf_biscuit').verdicts;
    await t.ensureVisible(find.text(verdicts[3].memberName));
    await t.pumpAndSettle();
    await t.tap(find.text(verdicts[3].memberName));
    await t.pumpAndSettle();
    await _tapSave(t);
    expect(h.client.logged.single.memberId, verdicts[3].memberId);
  });

  testWidgets('offline: closes with the queued result', (t) async {
    final h = await _open(t, servingSizeG: 25, responses: [networkError()]);
    await _tapSave(t);
    expect(h.result, isA<MealQueued>());
    expect(h.queue.rows, hasLength(1));
  });

  testWidgets('a refusal stays open with the localized error', (t) async {
    final h = await _open(
      t,
      servingSizeG: 25,
      responses: [apiError(422, 'serving_size_unknown')],
    );
    await _tapSave(t);
    expect(h.closed, isFalse);
    expect(find.text(en.errorServingSizeUnknown), findsOneWidget);
    expect(h.queue.rows, isEmpty);
  });

  testWidgets('verdict statuses are not shown in the sheet (no health data)', (
    t,
  ) async {
    await _open(t, servingSizeG: 25);
    for (final s in [en.statusAvoid, en.statusCaution, en.statusUnknown]) {
      expect(find.text(s), findsNothing);
    }
  });
}
