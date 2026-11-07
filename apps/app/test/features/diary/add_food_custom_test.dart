import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/foods/presentation/custom_food_form.dart';
import 'package:smartnutri_ai/features/foods/presentation/food_search_view.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_ai/features/recipes/presentation/recipe_builder_screen.dart';
import 'package:smartnutri_ai/features/settings/presentation/profile_screen.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import 'diary_harness.dart';

RecentItem _recent({
  String name = 'Buttermilk',
  RecentItemBasis basis = RecentItemBasis.g,
  num grams = 200,
  num? quantity,
  String? unit,
  RecentItemUnitSource? unitSource,
  String? customFoodId,
  String? recipeId,
  String? foodId,
  RecentItemSourceKind kind = RecentItemSourceKind.customFood,
}) => RecentItem(
  attribution: null,
  barcode: null,
  grade: null,
  grams: grams,
  lastEatenAt: DateTime.utc(2026, 11, 6, 8),
  mealSlotId: 'slot-breakfast',
  name: name,
  productId: null,
  sourceKind: kind,
  basis: basis,
  customFoodId: customFoodId,
  foodId: foodId,
  quantity: quantity,
  recipeId: recipeId,
  unit: unit,
  unitSource: unitSource,
);

DiaryEnv _env({List<RecentItem> recents = const [], FakeFoodsClient? foods}) {
  final env = DiaryEnv(foods: foods)..diary.recents = recents;
  env.slotsFromDay();
  return env;
}

Future<void> _open(WidgetTester t) async {
  await t.tap(find.byKey(DiaryScreen.addFabKey));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('an ml recent shows ml and logs millilitres', (t) async {
    final env = _env(
      recents: [_recent(basis: RecentItemBasis.ml, customFoodId: 'c1')],
    );
    await pumpDiary(t, env);
    await _open(t);
    expect(find.text('200 ml'), findsOneWidget);
    expect(find.text('200 g'), findsNothing);
    await t.tap(find.byKey(AddFoodSheet.recentKey('c1')));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.customFoodId, 'c1');
    expect(sent.productId, isNull);
    // Millilitres go as ml, never as grams.
    expect(sent.grams, isNull);
    expect(sent.quantity, 200);
    expect(sent.unit, MealInUnit.ml);
  });

  testWidgets('a density recent shows approx with the resolved ml', (t) async {
    final env = _env(
      recents: [
        _recent(
          basis: RecentItemBasis.ml,
          grams: 310,
          quantity: 2,
          unit: 'glass',
          unitSource: RecentItemUnitSource.density,
          customFoodId: 'c1',
        ),
      ],
    );
    await pumpDiary(t, env);
    await _open(t);
    expect(find.text('2 glasses · ≈ 310 ml'), findsOneWidget);
    await t.tap(find.byKey(AddFoodSheet.recentKey('c1')));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.quantity, 2);
    expect(sent.unit, MealInUnit.glass);
  });

  testWidgets('a grams recent keeps its grams line and a portion is approx', (
    t,
  ) async {
    final env = _env(
      recents: [
        _recent(
          name: 'Roti',
          grams: 136,
          quantity: 2,
          unit: 'roti',
          unitSource: RecentItemUnitSource.portion,
          foodId: 'f1',
          kind: RecentItemSourceKind.food,
        ),
        _recent(
          name: 'Oats',
          grams: 40,
          unitSource: RecentItemUnitSource.grams,
          foodId: 'f2',
          kind: RecentItemSourceKind.food,
        ),
      ],
    );
    await pumpDiary(t, env);
    await _open(t);
    expect(find.text('2 rotis · ≈ 136 g'), findsOneWidget);
    expect(find.text('40 g'), findsOneWidget);
  });

  testWidgets('a retired dish from recents is refused with the copy', (
    t,
  ) async {
    final env = _env(
      recents: [
        _recent(
          name: 'Old dish',
          grams: 100,
          foodId: 'f9',
          kind: RecentItemSourceKind.food,
        ),
      ],
    );
    env.meals.logResponses.add(apiRefusal422('food_retired'));
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.recentKey('f9')));
    await t.pumpAndSettle();
    expect(find.text(en.errorFoodRetired), findsOneWidget);
    // Refused, so not queued and the sheet stays open.
    expect(env.queue.rows, isEmpty);
    expect(find.byKey(AddFoodSheet.recentKey('f9')), findsOneWidget);
  });

  testWidgets('search shows my foods first and logs custom_food_id', (t) async {
    final foods = FakeFoodsClient(
      search: FoodSearchOut(
        failedSources: const [],
        items: [
          foodHit('f1', 'Toor dal, cooked'),
          foodHit(
            'c1',
            'Homemade ladoo',
            kind: FoodHitKind.customFood,
            group: FoodHitGroup.mine,
            attributions: const [],
          ),
          foodHit(
            'r1',
            'Rice and dal',
            kind: FoodHitKind.recipe,
            group: FoodHitGroup.mine,
            attributions: const [],
          ),
        ],
        partial: false,
      ),
      details: {
        'f1': foodDetail(),
        'c1': foodDetail(
          id: 'c1',
          name: 'Homemade ladoo',
          kind: FoodDetailOutKind.customFood,
          defaultUnit: 'g',
          attributions: const [],
          units: [unitOut('g', 1, kind: FoodUnitOutKind.mass)],
        ),
        'r1': foodDetail(
          id: 'r1',
          name: 'Rice and dal',
          kind: FoodDetailOutKind.recipe,
          defaultUnit: 'serving',
          units: [unitOut('serving', 110)],
        ),
      },
    );
    final env = _env(foods: foods);
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.segmentKey('search')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(FoodSearchView.fieldKey), 'ladoo');
    await t.pump(FoodSearchView.debounce);
    await t.pumpAndSettle();
    expect(
      find.descendant(
        of: find.byKey(FoodSearchView.groupKey('mine')),
        matching: find.text(en.foodsGroupMine),
      ),
      findsOneWidget,
    );
    expect(find.text(en.foodsKindCustomFood), findsOneWidget);
    expect(find.text(en.foodsKindRecipe), findsOneWidget);
    // Mine comes first.
    expect(
      t.getTopLeft(find.byKey(FoodSearchView.groupKey('mine'))).dy,
      lessThan(t.getTopLeft(find.byKey(FoodSearchView.groupKey('indian'))).dy),
    );

    await t.tap(
      find.byKey(
        FoodSearchView.hitKey(foodHit('c1', 'x', kind: FoodHitKind.customFood)),
      ),
    );
    await t.pumpAndSettle();
    expect(find.byType(PortionPickerSheet), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.customFoodId, 'c1');
    expect(sent.foodId, isNull);
    expect(sent.recipeId, isNull);
    expect(env.events.where((e) => e.$1 == 'diary_entry_added').single.$2, {
      'method': 'custom',
    });
  });

  testWidgets('create segment opens the custom food form and the builder', (
    t,
  ) async {
    final env = _env();
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.segmentKey('create')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.newFoodKey));
    await t.pumpAndSettle();
    expect(find.byType(CustomFoodFormScreen), findsOneWidget);
    // Back to the diary, then the recipe builder.
    await t.pageBack();
    await t.pumpAndSettle();
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.segmentKey('create')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.newRecipeKey));
    await t.pumpAndSettle();
    expect(find.byType(RecipeBuilderScreen), findsOneWidget);
  });

  testWidgets('profile opens My foods', (t) async {
    final env = _env();
    final h = await pumpDiary(t, env, initial: '/profile');
    await t.tap(find.byKey(ProfileScreen.myFoodsKey));
    await t.pumpAndSettle();
    expect(h.router.state.uri.path, '/diary/my-foods');
    expect(find.text(en.foodsMyFoods), findsWidgets);
  });
}

Object apiRefusal422(String code) => apiError(422, code);
