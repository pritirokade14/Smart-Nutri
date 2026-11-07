import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/presentation/food_search_view.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_ai/features/recipes/presentation/recipe_builder_screen.dart';
import 'package:smartnutri_ai/features/recipes/presentation/recipe_nutrients.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_recipes.dart';
import '../diary/diary_harness.dart';

DiaryEnv _env({RecipeOut? recipe}) {
  final env = DiaryEnv(
    foods: FakeFoodsClient(
      search: FoodSearchOut(
        failedSources: const [],
        items: [
          foodHit('f1', 'Toor dal, cooked'),
          foodHit('f2', 'Jeera rice', isDish: true),
          foodHit(
            'r9',
            'Old recipe',
            kind: FoodHitKind.recipe,
            group: FoodHitGroup.mine,
          ),
        ],
        partial: false,
      ),
      details: {
        'f1': foodDetail(),
        'f2': foodDetail(id: 'f2', name: 'Jeera rice'),
        'r1': foodDetail(
          id: 'r1',
          name: 'Rice and dal',
          kind: FoodDetailOutKind.recipe,
          defaultUnit: 'serving',
          recipeIncomplete: const ['fibre_g'],
          per100: snapshotOf(const {'energy_kcal': 142.3, 'protein_g': 5}),
          units: [
            unitOut('g', 1, kind: FoodUnitOutKind.mass),
            unitOut('serving', 110),
          ],
        ),
      },
    ),
    recipes: FakeRecipesClient(recipe: recipe),
  )..slotsFromDay();
  return env;
}

Future<void> _addIngredient(WidgetTester t, String name, String query) async {
  await t.tap(find.byKey(RecipeBuilderScreen.addIngredientKey));
  await t.pumpAndSettle();
  await t.enterText(find.byKey(FoodSearchView.fieldKey), query);
  await t.pump(FoodSearchView.debounce);
  await t.pumpAndSettle();
  await t.tap(find.text(name));
  await t.pumpAndSettle();
}

Future<void> _savePicker(WidgetTester t) async {
  await t.tap(find.byKey(PortionPickerSheet.saveKey));
  await t.pumpAndSettle();
}

ButtonStyleButton _save(WidgetTester t) =>
    t.widget<ButtonStyleButton>(find.byKey(RecipeBuilderScreen.saveKey));

void main() {
  testWidgets('adds ingredient through picker without logging', (t) async {
    final env = _env();
    await pumpDiary(t, env, initial: '/diary/recipes/new');
    await _addIngredient(t, 'Toor dal, cooked', 'dal');
    // The picker is for an amount only: no meal to choose.
    expect(find.byType(PortionPickerSheet), findsOneWidget);
    for (final s in env.slots.items) {
      expect(find.byKey(PortionPickerSheet.slotKey(s.id)), findsNothing);
    }
    await _savePicker(t);
    expect(find.byType(PortionPickerSheet), findsNothing);
    expect(
      find.descendant(
        of: find.byKey(RecipeBuilderScreen.ingredientsKey),
        matching: find.text('Toor dal, cooked'),
      ),
      findsOneWidget,
    );
    // Nothing was logged and no diary event was sent.
    expect(env.meals.logged, isEmpty);
    expect(env.queue.rows, isEmpty);
    expect(env.events.where((e) => e.$1 == 'diary_entry_added'), isEmpty);
  });

  testWidgets('a recipe cannot be an ingredient of a recipe', (t) async {
    await pumpDiary(t, _env(), initial: '/diary/recipes/new');
    await t.tap(find.byKey(RecipeBuilderScreen.addIngredientKey));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(FoodSearchView.fieldKey), 'dal');
    await t.pump(FoodSearchView.debounce);
    await t.pumpAndSettle();
    expect(find.text('Toor dal, cooked'), findsOneWidget);
    expect(find.text('Old recipe'), findsNothing);
  });

  testWidgets('no numbers before save', (t) async {
    await pumpDiary(t, _env(), initial: '/diary/recipes/new');
    await _addIngredient(t, 'Toor dal, cooked', 'dal');
    await _savePicker(t);
    expect(find.byType(RecipeNutrients), findsNothing);
    expect(find.byKey(RecipeNutrients.per100Key), findsNothing);
    expect(find.text(en.recipesPer100g), findsNothing);
    expect(find.text(en.recipesPerServing), findsNothing);
    expect(find.byKey(RecipeBuilderScreen.logKey), findsNothing);
    expect(
      texts(t).where((s) => s.contains('kcal') || s.contains('At least')),
      isEmpty,
    );
    expect(find.text(en.recipesCookedWeightTip), findsOneWidget);
  });

  testWidgets('create a recipe from two ingredients, then see at least', (
    t,
  ) async {
    final env = _env();
    await pumpDiary(t, env, initial: '/diary/recipes/new');
    expect(_save(t).onPressed, isNull);
    await t.enterText(find.byKey(RecipeBuilderScreen.nameKey), 'Rice and dal');
    await _addIngredient(t, 'Toor dal, cooked', 'dal');
    await _savePicker(t);
    await _addIngredient(t, 'Jeera rice', 'rice');
    await _savePicker(t);
    await t.enterText(find.byKey(RecipeBuilderScreen.servingsKey), '2');
    await t.enterText(find.byKey(RecipeBuilderScreen.cookedWeightKey), '300');
    await t.pump();
    await t.ensureVisible(find.byKey(RecipeBuilderScreen.saveKey));
    await t.tap(find.byKey(RecipeBuilderScreen.saveKey));
    await t.pumpAndSettle();

    final sent = env.recipes.created.single;
    expect(sent.name, 'Rice and dal');
    expect(sent.servings, 2);
    expect(sent.cookedWeightG, 300);
    expect(sent.ingredients.map((i) => i.foodId), ['f1', 'f2']);
    expect(sent.clientId, isNotNull);
    // The API's numbers, with the lower bound marked.
    final fibre = find.byKey(RecipeNutrients.rowKey('per-100g', 'fibre_g'));
    expect(
      find.descendant(
        of: fibre,
        matching: find.text(en.diaryWeekAtLeast(en.targetsGValue('2.1'))),
      ),
      findsOneWidget,
    );
    expect(find.byKey(RecipeBuilderScreen.logKey), findsOneWidget);
  });

  testWidgets('unavailable ingredient blocks save', (t) async {
    final env = _env(
      recipe: recipeFromFixture(
        'recipe_missing_fibre',
        ingredients: [
          recipeIngredientOut(),
          recipeIngredientOut(
            position: 1,
            name: 'My ladoo',
            available: false,
            foodId: null,
            customFoodId: 'c1',
          ),
        ],
      ),
    );
    await pumpDiary(t, env, initial: '/diary/recipes/r1');
    expect(find.byKey(RecipeBuilderScreen.unavailableKey(1)), findsOneWidget);
    expect(find.text(en.recipesIngredientUnavailable), findsOneWidget);
    expect(find.byKey(RecipeBuilderScreen.unavailableKey(0)), findsNothing);
    expect(_save(t).onPressed, isNull);
    // Removing the deleted one lets the recipe be saved again.
    await t.tap(find.byKey(RecipeBuilderScreen.removeKey(1)));
    await t.pump();
    expect(_save(t).onPressed, isNotNull);
    await t.ensureVisible(find.byKey(RecipeBuilderScreen.saveKey));
    await t.tap(find.byKey(RecipeBuilderScreen.saveKey));
    await t.pumpAndSettle();
    final (id, body) = env.recipes.updated.single;
    expect(id, 'r1');
    expect(body.ingredients.single.foodId, 'f-rice');
  });

  testWidgets('log a serving opens recipe picker', (t) async {
    final env = _env();
    await pumpDiary(t, env, initial: '/diary/recipes/r1');
    // Loaded: the API's numbers show with the lower bound marked.
    expect(find.byType(RecipeNutrients), findsOneWidget);
    await t.ensureVisible(find.byKey(RecipeBuilderScreen.logKey));
    await t.tap(find.byKey(RecipeBuilderScreen.logKey));
    await t.pumpAndSettle();
    expect(find.byType(PortionPickerSheet), findsOneWidget);
    expect(env.foods.gets, contains('r1'));
    // The strict recipe numbers: the unknown fibre says so.
    expect(find.byKey(PortionPickerSheet.recipeIncompleteKey), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.recipeId, 'r1');
    expect(sent.foodId, isNull);
    expect(sent.quantity, 1);
    expect(sent.unit, MealInUnit.serving);
    expect(env.events.where((e) => e.$1 == 'diary_entry_added').single.$2, {
      'method': 'recipe',
    });
  });

  testWidgets('a recipe api error shows its message', (t) async {
    final env = _env();
    await pumpDiary(t, env, initial: '/diary/recipes/new');
    await t.enterText(find.byKey(RecipeBuilderScreen.nameKey), 'X');
    await _addIngredient(t, 'Toor dal, cooked', 'dal');
    await _savePicker(t);
    env.recipes.error = apiRefusal('recipe_weight_invalid');
    await t.ensureVisible(find.byKey(RecipeBuilderScreen.saveKey));
    await t.tap(find.byKey(RecipeBuilderScreen.saveKey));
    await t.pumpAndSettle();
    expect(
      find.descendant(
        of: find.byKey(RecipeBuilderScreen.errorKey),
        matching: find.text(en.errorRecipeWeightInvalid),
      ),
      findsOneWidget,
    );
  });
}
