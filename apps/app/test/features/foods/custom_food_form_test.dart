import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/presentation/custom_food_form.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_recipes.dart';
import '../../support/fake_user_types.dart';
import 'foods_harness.dart';

Future<void> _type(WidgetTester t, Key key, String text) async {
  await t.enterText(find.byKey(key), text);
  await t.pump();
}

Future<void> _save(WidgetTester t) async {
  await t.tap(find.byKey(CustomFoodFormScreen.saveKey));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('blank sends absent not zero', (t) async {
    final customFoods = FakeCustomFoodsClient();
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const CustomFoodFormScreen(),
    );
    // The form says what blank means.
    expect(find.text(en.foodsBlankIsUnknown), findsOneWidget);
    await _type(t, CustomFoodFormScreen.nameKey, 'Homemade ladoo');
    await _type(t, CustomFoodFormScreen.nutrientKey('energy_kcal'), '400');
    await _save(t);

    final body = customFoods.created.single;
    expect(body.name, 'Homemade ladoo');
    expect(body.valuesPer, CustomFoodInValuesPer.value100);
    expect(body.servingG, isNull);
    expect(body.nutrients.energyKcal, 400);
    // Every other nutrient is absent, never 0.
    expect(body.nutrients.proteinG, isNull);
    expect(body.nutrients.sugarsG, isNull);
    expect(body.nutrients.sodiumMg, isNull);
    final sent = body.nutrients.toJson();
    expect(sent.values.where((v) => v == 0), isEmpty);
    expect(body.barcode, isNull);
    expect(body.brand, isNull);
    expect(body.portions, isNull);
    expect(body.densityGPerMl, isNull);
    // One id per form, so a retry never stores the food twice.
    expect(body.clientId, isNotNull);
    // Saved: the screen closes.
    expect(find.byType(CustomFoodFormScreen), findsNothing);
  });

  testWidgets('per serving sends values_per serving', (t) async {
    final customFoods = FakeCustomFoodsClient();
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const CustomFoodFormScreen(),
    );
    await t.tap(
      find.descendant(
        of: find.byKey(CustomFoodFormScreen.valuesPerKey),
        matching: find.text(en.foodsValuesPerServing),
      ),
    );
    await t.pumpAndSettle();
    await _type(t, CustomFoodFormScreen.nameKey, 'Protein bar');
    await _type(t, CustomFoodFormScreen.servingKey, '40');
    await _type(t, CustomFoodFormScreen.nutrientKey('energy_kcal'), '160');
    await _type(t, CustomFoodFormScreen.nutrientKey('protein_g'), '12');
    await _save(t);
    final body = customFoods.created.single;
    expect(body.valuesPer, CustomFoodInValuesPer.serving);
    expect(body.servingG, 40);
    expect(body.nutrients.proteinG, 12);
  });

  testWidgets('ml basis sends density and the ml basis', (t) async {
    final customFoods = FakeCustomFoodsClient();
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const CustomFoodFormScreen(),
    );
    expect(find.byKey(CustomFoodFormScreen.densityKey), findsNothing);
    await t.tap(find.text(en.customFoodBasisMl));
    await t.pumpAndSettle();
    expect(find.text(en.foodsValuesPer100ml), findsOneWidget);
    await _type(t, CustomFoodFormScreen.nameKey, 'Buttermilk');
    await _type(t, CustomFoodFormScreen.nutrientKey('energy_kcal'), '40');
    await _type(t, CustomFoodFormScreen.densityKey, '1.03');
    await _save(t);
    final body = customFoods.created.single;
    expect(body.basis, CustomFoodInBasis.ml);
    expect(body.densityGPerMl, 1.03);
  });

  testWidgets('an unparsable number blocks the save', (t) async {
    final customFoods = FakeCustomFoodsClient();
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const CustomFoodFormScreen(),
    );
    await _type(t, CustomFoodFormScreen.nameKey, 'X');
    await _type(t, CustomFoodFormScreen.nutrientKey('energy_kcal'), '1,5');
    await _save(t);
    expect(customFoods.created, isEmpty);
    expect(find.text(en.errorValidationError), findsOneWidget);
  });

  testWidgets('api errors map to messages', (t) async {
    for (final (code, message) in [
      ('custom_food_nutrients_empty', en.errorCustomFoodNutrientsEmpty),
      ('barcode_already_used', en.errorBarcodeAlreadyUsed),
      ('implausible_value', en.errorImplausibleValue),
      ('unit_grams_unknown', en.errorUnitGramsUnknown),
    ]) {
      final customFoods = FakeCustomFoodsClient()
        ..error = apiRefusal(
          code,
          details: {
            'fields': ['body.nutrients.sugars_g'],
          },
        );
      await pumpScreen(
        t,
        FakeUserTypesApi(customFoods: customFoods),
        const CustomFoodFormScreen(),
      );
      await _type(t, CustomFoodFormScreen.nameKey, 'Ladoo');
      await _type(t, CustomFoodFormScreen.nutrientKey('energy_kcal'), '400');
      await _save(t);
      expect(
        find.descendant(
          of: find.byKey(CustomFoodFormScreen.errorKey),
          matching: find.text(message),
        ),
        findsOneWidget,
        reason: code,
      );
      // The form stays open with what was typed.
      expect(find.byType(CustomFoodFormScreen), findsOneWidget);
      if (code == 'implausible_value') {
        // The field the API named is highlighted.
        expect(
          find.descendant(
            of: find.byKey(CustomFoodFormScreen.nutrientKey('sugars_g')),
            matching: find.text(en.errorImplausibleValue),
          ),
          findsOneWidget,
        );
        // The banner and the one named field.
        expect(find.text(en.errorImplausibleValue), findsNWidgets(2));
      }
    }
  });

  testWidgets('edit prefills and saves with a full replace', (t) async {
    final customFoods = FakeCustomFoodsClient();
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      CustomFoodFormScreen(
        food: customFoodOut(brand: 'Amma', energy: 410, protein: 6),
      ),
    );
    expect(find.text('Homemade ladoo'), findsOneWidget);
    expect(find.text('410'), findsOneWidget);
    // An empty field stays empty: unknown, not 0.
    await _type(t, CustomFoodFormScreen.nutrientKey('protein_g'), '');
    await _save(t);
    final (id, body) = customFoods.updated.single;
    expect(id, 'c1');
    expect(body.nutrients.energyKcal, 410);
    expect(body.nutrients.proteinG, isNull);
    expect(body.brand, 'Amma');
  });

  testWidgets('delete shows history kept note', (t) async {
    final customFoods = FakeCustomFoodsClient(items: [customFoodOut()]);
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      CustomFoodFormScreen(food: customFoodOut()),
    );
    await t.tap(find.byKey(CustomFoodFormScreen.deleteKey));
    await t.pumpAndSettle();
    expect(find.byKey(CustomFoodFormScreen.historyKeptKey), findsOneWidget);
    expect(find.text(en.customFoodHistoryKept), findsOneWidget);
    expect(find.text(en.customFoodDeleteConfirm), findsOneWidget);
    expect(customFoods.deleted, isEmpty);
    await t.tap(find.byKey(CustomFoodFormScreen.deleteConfirmKey));
    await t.pumpAndSettle();
    expect(customFoods.deleted, ['c1']);
    expect(find.byType(CustomFoodFormScreen), findsNothing);
  });

  testWidgets('a create form has no delete', (t) async {
    await pumpScreen(t, FakeUserTypesApi(), const CustomFoodFormScreen());
    expect(find.byKey(CustomFoodFormScreen.deleteKey), findsNothing);
  });
}
