import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import 'foods_harness.dart';

Future<List<PortionChoice>> pumpPicker(
  WidgetTester t,
  FakeFoodsClient foods, {
  Object? saveError,
}) async {
  final saved = <PortionChoice>[];
  await pumpOver(
    t,
    foods,
    PortionPickerSheet(
      food: (kind: FoodKindPath.food, id: 'f1'),
      name: 'Toor dal, cooked',
      memberId: 'm1',
      onSave: (c) async {
        if (saveError != null) throw saveError;
        saved.add(c);
        return const MealQueued('c1');
      },
    ),
  );
  return saved;
}

void main() {
  testWidgets('preview shows the same eight rows as the web', (t) async {
    await pumpPicker(t, FakeFoodsClient());
    for (final k in const [
      'energy_kcal',
      'protein_g',
      'carbs_g',
      'sugars_g',
      'fat_g',
      'sat_fat_g',
      'fibre_g',
      'salt_g',
    ]) {
      expect(find.byKey(PortionPickerSheet.previewKey(k)), findsOneWidget);
    }
    // 1 katori of dal = 142 g: fibre 4 per 100 g -> 5.7 g; unit shown.
    expect(
      find.descendant(
        of: find.byKey(PortionPickerSheet.previewKey('fibre_g')),
        matching: find.text(en.targetsGValue('5.7')),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(PortionPickerSheet.previewKey('energy_kcal')),
        matching: find.text(en.targetsKcalValue('170.4')),
      ),
      findsOneWidget,
    );
  });

  testWidgets("picker offers only the API's units", (t) async {
    await pumpPicker(t, FakeFoodsClient());
    expect(find.byKey(PortionPickerSheet.unitKey('g')), findsOneWidget);
    expect(find.byKey(PortionPickerSheet.unitKey('katori')), findsOneWidget);
    expect(
      find.byKey(PortionPickerSheet.unitKey('katori_medium')),
      findsOneWidget,
    );
    // Not resolved by the API: never offered.
    expect(find.byKey(PortionPickerSheet.unitKey('cup')), findsNothing);
    expect(find.byKey(PortionPickerSheet.unitKey('roti')), findsNothing);
    // Katori sizes show the API's ml.
    expect(find.textContaining('155 ml'), findsOneWidget);
    expect(find.textContaining('200 ml'), findsOneWidget);
  });

  testWidgets('default unit preselected', (t) async {
    final saved = await pumpPicker(t, FakeFoodsClient());
    final chip = t.widget<ChoiceChip>(
      find.byKey(PortionPickerSheet.unitKey('katori')),
    );
    expect(chip.selected, isTrue);
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    expect(saved.single.unit, 'katori');
    expect(saved.single.quantity, 1);
  });

  testWidgets('grams always shown', (t) async {
    await pumpPicker(t, FakeFoodsClient());
    expect(find.text('1 katori ≈ 142 g'), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.unitKey('katori_medium')));
    await t.pumpAndSettle();
    expect(find.text('1 medium katori ≈ 110.05 g'), findsOneWidget);
  });

  testWidgets('fraction chips set the quantity and the preview follows', (
    t,
  ) async {
    await pumpPicker(t, FakeFoodsClient());
    // 1 katori = 142 g of dal at 120 kcal/100 g.
    expect(find.text('170.4 kcal'), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.fractionKey('1½')));
    await t.pumpAndSettle();
    expect(find.text('255.6 kcal'), findsOneWidget);
    expect(find.text(en.foodsPreviewNote), findsOneWidget);
  });

  testWidgets('edit grams saves override and reloads', (t) async {
    final foods = FakeFoodsClient();
    await pumpPicker(t, foods);
    final before = foods.gets.length;
    await t.tap(find.byKey(PortionPickerSheet.editGramsKey));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(PortionPickerSheet.gramsInputKey), '150');
    await t.pump();
    await t.tap(find.byKey(PortionPickerSheet.gramsConfirmKey));
    await t.pumpAndSettle();
    expect(foods.puts.single, ('f1', 'katori', 150));
    expect(foods.gets.length, greaterThan(before));
    expect(find.text('1 katori ≈ 150 g'), findsOneWidget);
    expect(find.text(en.unitResetGrams), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.resetGramsKey));
    await t.pumpAndSettle();
    expect(foods.deletes.single, ('f1', 'katori'));
    expect(find.text('1 katori ≈ 142 g'), findsOneWidget);
  });

  testWidgets('settable unit sets grams', (t) async {
    final foods = FakeFoodsClient(
      details: {
        'f1': foodDetail(settableUnits: ['cup']),
      },
    );
    await pumpPicker(t, foods);
    expect(find.byKey(PortionPickerSheet.unitKey('cup')), findsNothing);
    expect(find.text(en.unitSetGrams('cup')), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.setGramsKey('cup')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(PortionPickerSheet.gramsInputKey), '180');
    await t.pump();
    await t.tap(find.byKey(PortionPickerSheet.gramsConfirmKey));
    await t.pumpAndSettle();
    expect(foods.puts.single, ('f1', 'cup', 180));
    // It resolves now and is the selected unit.
    expect(find.byKey(PortionPickerSheet.unitKey('cup')), findsOneWidget);
    expect(find.text('1 cup ≈ 180 g'), findsOneWidget);
    expect(find.byKey(PortionPickerSheet.setGramsKey('cup')), findsNothing);
  });

  testWidgets('unknown nutrient shows not known', (t) async {
    final foods = FakeFoodsClient(
      details: {
        'f1': foodDetail(
          per100: const NutrientSnapshot(
            carbsG: 15,
            energyKcal: 120,
            fatG: 3,
            fibreG: null,
            proteinG: 7,
            saltG: null,
            satFatG: null,
            sugarsG: null,
          ),
        ),
      },
    );
    await pumpPicker(t, foods);
    final row = find.byKey(PortionPickerSheet.previewKey('sugars_g'));
    expect(
      find.descendant(of: row, matching: find.text(en.foodsNotKnown)),
      findsOneWidget,
    );
    expect(
      find.descendant(of: row, matching: find.text('0.0 g')),
      findsNothing,
    );
    expect(find.text('9.9 g'), findsOneWidget);
  });

  testWidgets('hide_all shows no preview digits', (t) async {
    final foods = FakeFoodsClient(
      details: {
        'f1': foodDetail(per100: allNull(), hideEnergy: true, hideMacros: true),
      },
    );
    await pumpPicker(t, foods);
    expect(find.byKey(PortionPickerSheet.previewKeyAll), findsNothing);
    expect(find.text(en.foodsNotKnown), findsNothing);
    expect(find.text(en.foodsPreviewNote), findsNothing);
    // Only grams and the quantity appear.
    expect(find.text('1 katori ≈ 142 g'), findsOneWidget);
    expect(find.byKey(PortionPickerSheet.quantityKey), findsOneWidget);
    for (final text in shownTexts(t)) {
      expect(text.contains('kcal'), isFalse, reason: text);
    }
  });

  testWidgets('hide_energy hides only energy', (t) async {
    final foods = FakeFoodsClient(
      details: {
        'f1': foodDetail(
          per100: const NutrientSnapshot(
            carbsG: 15,
            energyKcal: null,
            fatG: 3,
            fibreG: 4,
            proteinG: 7,
            saltG: 0.5,
            satFatG: null,
            sugarsG: 2.5,
          ),
          hideEnergy: true,
        ),
      },
    );
    await pumpPicker(t, foods);
    expect(
      find.byKey(PortionPickerSheet.previewKey('energy_kcal')),
      findsNothing,
    );
    expect(
      find.byKey(PortionPickerSheet.previewKey('protein_g')),
      findsOneWidget,
    );
    // Saturated fat is a preview row now (the web's eight): unknown says so.
    expect(
      find.descendant(
        of: find.byKey(PortionPickerSheet.previewKey('sat_fat_g')),
        matching: find.text(en.foodsNotKnown),
      ),
      findsOneWidget,
    );
    expect(find.text(en.foodsNotKnown), findsOneWidget);
  });

  testWidgets('dish shows ingredients and review note', (t) async {
    final foods = FakeFoodsClient(
      details: {
        'f1': foodDetail(
          name: 'Dal tadka',
          attributions: const [
            'attribution.smartnutri_recipe',
            'attribution.usda_fdc',
          ],
          dish: const DishOut(
            cookedWeightG: 300,
            servings: null,
            ingredients: [
              DishIngredientOut(name: 'Toor dal', grams: 80),
              DishIngredientOut(name: 'Ghee', grams: 10),
            ],
          ),
        ),
      },
    );
    await pumpPicker(t, foods);
    expect(find.text(en.foodsDishIngredients), findsOneWidget);
    expect(find.text('Toor dal · 80 g'), findsOneWidget);
    expect(find.text('Ghee · 10 g'), findsOneWidget);
    expect(find.text(en.foodsReviewPending), findsOneWidget);
    expect(find.text(en.attributionUsdaFdc), findsOneWidget);
    expect(find.text(en.attributionSmartnutriRecipe), findsOneWidget);
  });

  testWidgets('unit_grams_unknown maps to message', (t) async {
    await pumpPicker(
      t,
      FakeFoodsClient(),
      saveError: MealsFailure('unit_grams_unknown', apiError(422, 'x')),
    );
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorUnitGramsUnknown), findsOneWidget);
    // Stays open so the user can pick another unit.
    expect(find.byKey(PortionPickerSheet.saveKey), findsOneWidget);
  });

  testWidgets('quantity_out_of_range maps to message', (t) async {
    await pumpPicker(
      t,
      FakeFoodsClient(),
      saveError: const MealsFailure('quantity_out_of_range'),
    );
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorQuantityOutOfRange), findsOneWidget);
  });
}
