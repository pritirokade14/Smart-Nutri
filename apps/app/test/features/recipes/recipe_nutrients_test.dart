import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/features/recipes/presentation/recipe_nutrients.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_recipes.dart';
import '../foods/foods_harness.dart';

Future<void> _pump(WidgetTester t, RecipeOut r, {String locale = 'en'}) =>
    pumpOver(
      t,
      FakeFoodsClient(),
      SingleChildScrollView(child: RecipeNutrients(recipe: r)),
      locale: locale,
    );

Text _text(WidgetTester t, Finder row) =>
    t.widget<Text>(find.descendant(of: row, matching: find.byType(Text)).last);

void main() {
  testWidgets('renders recipes/expected recipe_missing_fibre', (t) async {
    await _pump(t, recipeFromFixture('recipe_missing_fibre'));
    final fibre = find.byKey(RecipeNutrients.rowKey('per-100g', 'fibre_g'));
    // 2.1 g is only what the other ingredients add up to.
    expect(
      find.descendant(
        of: fibre,
        matching: find.text(en.diaryWeekAtLeast(en.targetsGValue('2.1'))),
      ),
      findsOneWidget,
    );
    expect(
      find.byKey(RecipeNutrients.markerKey('per-100g', 'fibre_g')),
      findsOneWidget,
    );
    // A complete nutrient is a plain number with no marker.
    final protein = find.byKey(RecipeNutrients.rowKey('per-100g', 'protein_g'));
    expect(
      find.descendant(of: protein, matching: find.text(en.targetsGValue('5'))),
      findsOneWidget,
    );
    expect(
      find.byKey(RecipeNutrients.markerKey('per-100g', 'protein_g')),
      findsNothing,
    );
    expect(find.text(en.recipesIncomplete), findsOneWidget);
    // No servings in this fixture: no per-serving block.
    expect(find.byKey(RecipeNutrients.perServingKey), findsNothing);
  });

  testWidgets('incomplete recipe nutrient renders at least, never a plain '
      'number', (t) async {
    for (final name in const [
      'recipe_missing_fibre',
      'recipe_all_unknown_sat_fat',
    ]) {
      final recipe = recipeFromFixture(name);
      await _pump(t, recipe);
      for (final k in recipe.incompleteNutrients) {
        final row = find.byKey(RecipeNutrients.rowKey('per-100g', k));
        final shown = _text(t, row);
        final data = shown.data!;
        // A partial value reads "At least ...", an unknown one "Not known".
        expect(
          data == en.foodsNotKnown || data.startsWith('At least'),
          isTrue,
          reason: '$name $k: $data',
        );
        expect(
          find.byKey(RecipeNutrients.markerKey('per-100g', k)),
          findsOneWidget,
        );
        // Grey, never the colour of a complete value.
        if (data != en.foodsNotKnown) {
          final c = SnColors.of(t.element(row));
          expect(shown.style?.color, c.textSecondary);
        }
      }
    }
  });

  testWidgets('all-unknown sat fat says not known with the marker', (t) async {
    await _pump(t, recipeFromFixture('recipe_all_unknown_sat_fat'));
    final row = find.byKey(RecipeNutrients.rowKey('per-100g', 'sat_fat_g'));
    expect(
      find.descendant(of: row, matching: find.text(en.foodsNotKnown)),
      findsOneWidget,
    );
    expect(
      find.byKey(RecipeNutrients.markerKey('per-100g', 'sat_fat_g')),
      findsOneWidget,
    );
  });

  testWidgets('complete recipe with servings shows both blocks, no marker', (
    t,
  ) async {
    await _pump(t, recipeFromFixture('recipe_servings_4'));
    expect(find.byKey(RecipeNutrients.per100Key), findsOneWidget);
    expect(find.byKey(RecipeNutrients.perServingKey), findsOneWidget);
    expect(find.byKey(RecipeNutrients.noteKey), findsNothing);
    expect(find.textContaining('At least'), findsNothing);
    final kcal = find.byKey(
      RecipeNutrients.rowKey('per-serving', 'energy_kcal'),
    );
    expect(
      find.descendant(
        of: kcal,
        matching: find.text(en.targetsKcalValue('138.2')),
      ),
      findsOneWidget,
    );
  });

  testWidgets('hide_all shows no digits', (t) async {
    final r = recipeFromFixture(
      'recipe_servings_4',
      hideEnergy: true,
      hideMacros: true,
    );
    await _pump(t, r);
    expect(shownTexts(t).where((s) => RegExp(r'\d').hasMatch(s)), isEmpty);
    expect(find.byKey(RecipeNutrients.per100Key), findsNothing);
    expect(find.text(en.foodsNotKnown), findsNothing);
  });

  testWidgets('hide energy only keeps the macro rows', (t) async {
    await _pump(t, recipeFromFixture('recipe_servings_4', hideEnergy: true));
    expect(
      find.byKey(RecipeNutrients.rowKey('per-100g', 'energy_kcal')),
      findsNothing,
    );
    expect(
      find.byKey(RecipeNutrients.rowKey('per-100g', 'protein_g')),
      findsOneWidget,
    );
  });

  testWidgets('hindi renders the same marker', (t) async {
    await _pump(t, recipeFromFixture('recipe_missing_fibre'), locale: 'hi');
    expect(
      find.byKey(RecipeNutrients.markerKey('per-100g', 'fibre_g')),
      findsOneWidget,
    );
  });
}
