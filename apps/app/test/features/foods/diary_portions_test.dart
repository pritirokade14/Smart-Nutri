import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/edit_entry_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/entry_tile.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import 'foods_harness.dart';

MealOut _entry({
  String basis = 'g',
  num grams = 136,
  List<String> attributions = const ['attribution.usda_fdc'],
  Map<String, Object?>? extra,
}) => MealOut.fromJson(
  jsonDecode(
        jsonEncode({
          ...mealOut(productName: 'Roti', grams: grams).toJson(),
          'nutrients': mealOut().nutrients.toJson(),
          'source_kind': 'food',
          'food_id': 'f1',
          'quantity': 2,
          'unit': 'roti',
          'basis': basis,
          'attributions': attributions,
          'portion_units': [
            {'code': 'g', 'grams_per_unit': 1},
            {'code': 'roti', 'grams_per_unit': 68},
            {'code': 'piece', 'grams_per_unit': 40},
          ],
          ...?extra,
        }),
      )
      as Map<String, Object?>,
);

void main() {
  testWidgets('entry shows the portion line and the USDA credit', (t) async {
    await pumpOver(t, FakeFoodsClient(), EntryTile(entry: _entry()));
    expect(find.text('2 rotis · 136 g'), findsOneWidget);
    expect(find.text(en.attributionUsdaFdc), findsOneWidget);
  });

  testWidgets('an ml entry shows ml', (t) async {
    await pumpOver(
      t,
      FakeFoodsClient(),
      EntryTile(entry: _entry(basis: 'ml', grams: 250)),
    );
    expect(find.text('2 rotis · 250 ml'), findsOneWidget);
  });

  testWidgets('a grams unit entry keeps the plain grams line', (t) async {
    await pumpOver(
      t,
      FakeFoodsClient(),
      EntryTile(entry: _entry(extra: {'unit': 'g', 'quantity': 136})),
    );
    expect(find.text(en.diaryGramsLine('136')), findsOneWidget);
  });

  testWidgets('a legacy entry keeps the grams line', (t) async {
    await pumpOver(t, FakeFoodsClient(), EntryTile(entry: mealOut(grams: 30)));
    expect(find.text(en.diaryGramsLine('30')), findsOneWidget);
  });

  testWidgets('edit sheet offers the units the entry resolved with', (t) async {
    await pumpOver(t, FakeFoodsClient(), EditEntrySheet(entry: _entry()));
    expect(find.byKey(EditEntrySheet.unitKey('roti')), findsOneWidget);
    expect(find.byKey(EditEntrySheet.unitKey('piece')), findsOneWidget);
    expect(find.byKey(EditEntrySheet.unitKey('cup')), findsNothing);
    expect(find.text('1 roti ≈ 68 g'), findsOneWidget);
    // No nutrient preview in the edit sheet.
    expect(find.textContaining('kcal'), findsNothing);
  });
}
