import 'dart:convert';
import 'dart:io';

import 'package:smartnutri_api/src/export.dart';

import 'fake_meals.dart' show apiError;

const _recipes = '../../packages/test-fixtures/recipes/expected';

NutrientSnapshot snapshotOf(Map<String, Object?> m) => NutrientSnapshot(
  carbsG: m['carbs_g'] as num?,
  energyKcal: m['energy_kcal'] as num?,
  fatG: m['fat_g'] as num?,
  fibreG: m['fibre_g'] as num?,
  proteinG: m['protein_g'] as num?,
  saltG: m['salt_g'] as num?,
  satFatG: m['sat_fat_g'] as num?,
  sugarsG: m['sugars_g'] as num?,
);

NutrientSnapshot noNutrients() => snapshotOf(const {});

/// A [RecipeOut] whose numbers are the shared fixture
/// `recipes/expected/<name>.json` (what the API returns for it).
RecipeOut recipeFromFixture(
  String name, {
  bool hideEnergy = false,
  bool hideMacros = false,
  List<RecipeIngredientOut>? ingredients,
}) {
  final f =
      jsonDecode(File('$_recipes/$name.json').readAsStringSync())
          as Map<String, Object?>;
  final hidden = hideEnergy && hideMacros;
  final per100 = Map<String, Object?>.from(f['per_100g']! as Map);
  final perServing = f['per_serving'] == null
      ? null
      : Map<String, Object?>.from(f['per_serving']! as Map);
  // A hidden number is null on the wire (the API redacts it).
  if (hidden) {
    per100.updateAll((_, _) => null);
    perServing?.updateAll((_, _) => null);
  }
  return RecipeOut(
    attributions: const ['attribution.usda_fdc'],
    basisWeightG: f['basis_weight_g']! as num,
    cookedWeightG: null,
    id: 'r1',
    incompleteNutrients: [
      for (final k in f['incomplete_nutrients']! as List) k as String,
    ],
    ingredients: ingredients ?? [recipeIngredientOut()],
    name: 'Rice and dal',
    numbersHidden: NumbersHidden(energy: hideEnergy, macros: hideMacros),
    per100g: snapshotOf(per100),
    perServing: perServing == null ? null : snapshotOf(perServing),
    servings: perServing == null ? null : 4,
    totalRawG: f['total_raw_g'] as num?,
    updatedAt: DateTime.utc(2026, 11, 7),
  );
}

RecipeIngredientOut recipeIngredientOut({
  int position = 0,
  String name = 'Rice',
  bool available = true,
  String? foodId = 'f-rice',
  String? customFoodId,
  num quantity = 150,
  String unit = 'g',
}) => RecipeIngredientOut(
  attribution: null,
  available: available,
  barcode: null,
  customFoodId: customFoodId,
  foodId: foodId,
  grams: quantity,
  name: name,
  position: position,
  productId: null,
  quantity: quantity,
  sourceKind: customFoodId != null
      ? RecipeIngredientOutSourceKind.customFood
      : RecipeIngredientOutSourceKind.food,
  unit: unit,
);

CustomFoodOut customFoodOut({
  String id = 'c1',
  String name = 'Homemade ladoo',
  String? brand,
  CustomFoodOutBasis basis = CustomFoodOutBasis.g,
  num? energy = 400,
  num? protein,
  EnteredOutValuesPer valuesPer = EnteredOutValuesPer.value100,
  num? servingG,
  num? density,
  String? barcode,
  List<CustomPortionOut> portions = const [],
}) => CustomFoodOut(
  barcode: barcode,
  basis: basis,
  brand: brand,
  createdAt: DateTime.utc(2026, 11, 7),
  densityGPerMl: density,
  entered: EnteredOut(
    nutrients: CustomNutrientsIn(energyKcal: energy, proteinG: protein),
    servingG: servingG,
    valuesPer: valuesPer,
  ),
  id: id,
  name: name,
  per100: snapshotOf({'energy_kcal': energy, 'protein_g': protein}),
  portions: portions,
  servingG: servingG,
  updatedAt: DateTime.utc(2026, 11, 7),
);

/// Pages `items` by `pageSize` with cursor `"<offset>"`. Records writes.
class FakeCustomFoodsClient implements CustomFoodsClient {
  FakeCustomFoodsClient({List<CustomFoodOut>? items, this.pageSize = 50})
    : items = items ?? [];

  final List<CustomFoodOut> items;
  final int pageSize;
  Object? error;
  final created = <CustomFoodIn>[];
  final updated = <(String, CustomFoodIn)>[];
  final deleted = <String>[];
  final cursors = <String?>[];

  @override
  Future<CustomFoodsOut> customFoodsList({String? cursor, int? limit}) async {
    cursors.add(cursor);
    final start = int.parse(cursor ?? '0');
    final end = (start + pageSize).clamp(0, items.length);
    return CustomFoodsOut(
      items: items.sublist(start, end),
      nextCursor: end < items.length ? '$end' : null,
    );
  }

  @override
  Future<CustomFoodOut> customFoodsCreate({required CustomFoodIn body}) async {
    final e = error;
    if (e != null) throw e;
    created.add(body);
    return customFoodOut(id: 'new', name: body.name);
  }

  @override
  Future<CustomFoodOut> customFoodsUpdate({
    required String foodId,
    required CustomFoodIn body,
  }) async {
    final e = error;
    if (e != null) throw e;
    updated.add((foodId, body));
    return customFoodOut(id: foodId, name: body.name);
  }

  @override
  Future<void> customFoodsDelete({required String foodId}) async {
    final e = error;
    if (e != null) throw e;
    deleted.add(foodId);
    items.removeWhere((f) => f.id == foodId);
  }
}

class FakeRecipesClient implements RecipesClient {
  FakeRecipesClient({
    List<RecipeSummaryOut>? items,
    this.pageSize = 50,
    RecipeOut? recipe,
  }) : items = items ?? [],
       recipe = recipe ?? recipeFromFixture('recipe_missing_fibre');

  final List<RecipeSummaryOut> items;
  final int pageSize;

  /// What get, create and update answer.
  RecipeOut recipe;
  Object? error;
  final created = <RecipeIn>[];
  final updated = <(String, RecipeIn)>[];
  final deleted = <String>[];

  @override
  Future<RecipesOut> recipesList({String? cursor, int? limit}) async {
    final start = int.parse(cursor ?? '0');
    final end = (start + pageSize).clamp(0, items.length);
    return RecipesOut(
      items: items.sublist(start, end),
      nextCursor: end < items.length ? '$end' : null,
    );
  }

  @override
  Future<RecipeOut> recipesGet({required String recipeId}) async {
    final e = error;
    if (e != null) throw e;
    return recipe;
  }

  @override
  Future<RecipeOut> recipesCreate({required RecipeIn body}) async {
    final e = error;
    if (e != null) throw e;
    created.add(body);
    return recipe;
  }

  @override
  Future<RecipeOut> recipesUpdate({
    required String recipeId,
    required RecipeIn body,
  }) async {
    final e = error;
    if (e != null) throw e;
    updated.add((recipeId, body));
    return recipe;
  }

  @override
  Future<void> recipesDelete({required String recipeId}) async {
    deleted.add(recipeId);
    items.removeWhere((r) => r.id == recipeId);
  }
}

RecipeSummaryOut recipeSummary(String id, String name) => RecipeSummaryOut(
  id: id,
  incompleteNutrients: const [],
  name: name,
  servings: 2,
  updatedAt: DateTime.utc(2026, 11, 7),
);

/// A 422 with the API's code, as the Dio client raises it.
Object apiRefusal(String code, {Map<String, Object?> details = const {}}) =>
    apiError(422, code, details: details);
