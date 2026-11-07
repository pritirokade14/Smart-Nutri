import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/foods/presentation/my_foods_screen.dart';

import '../../support/fake_recipes.dart';
import '../../support/fake_user_types.dart';
import 'foods_harness.dart';

void main() {
  testWidgets('lists custom foods and recipes', (t) async {
    final api = FakeUserTypesApi(
      customFoods: FakeCustomFoodsClient(
        items: [
          customFoodOut(id: 'c1', name: 'Ladoo'),
          customFoodOut(id: 'c2', name: 'Chivda', brand: 'Home'),
        ],
      ),
      recipes: FakeRecipesClient(items: [recipeSummary('r1', 'Rice and dal')]),
    );
    await pumpScreen(t, api, const MyFoodsScreen());
    expect(find.byKey(MyFoodsScreen.foodKey('c1')), findsOneWidget);
    expect(find.byKey(MyFoodsScreen.foodKey('c2')), findsOneWidget);
    expect(find.text('Chivda'), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.byKey(MyFoodsScreen.recipeKey('r1')), findsOneWidget);
    expect(find.text('Rice and dal'), findsOneWidget);
  });

  testWidgets('paginates', (t) async {
    final customFoods = FakeCustomFoodsClient(
      pageSize: 2,
      items: [
        for (var i = 1; i <= 5; i++) customFoodOut(id: 'c$i', name: 'Food $i'),
      ],
    );
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const MyFoodsScreen(),
    );
    // The next pages are asked for by their cursor until the end.
    expect(customFoods.cursors, [null, '2', '4']);
    for (var i = 1; i <= 5; i++) {
      expect(find.byKey(MyFoodsScreen.foodKey('c$i')), findsOneWidget);
    }
  });

  testWidgets('delete asks first, then removes and keeps the rest', (t) async {
    final customFoods = FakeCustomFoodsClient(
      items: [customFoodOut(id: 'c1', name: 'Ladoo')],
    );
    await pumpScreen(
      t,
      FakeUserTypesApi(customFoods: customFoods),
      const MyFoodsScreen(),
    );
    await t.tap(find.byKey(MyFoodsScreen.deleteFoodKey('c1')));
    await t.pumpAndSettle();
    expect(find.text(en.customFoodDeleteConfirm), findsOneWidget);
    expect(customFoods.deleted, isEmpty);
    await t.tap(find.byKey(const Key('my-foods-delete-confirm')));
    await t.pumpAndSettle();
    expect(customFoods.deleted, ['c1']);
    expect(find.byKey(MyFoodsScreen.foodKey('c1')), findsNothing);
  });

  testWidgets('an empty recipe list says so', (t) async {
    await pumpScreen(t, FakeUserTypesApi(), const MyFoodsScreen());
    expect(find.byKey(MyFoodsScreen.emptyKey), findsOneWidget);
    expect(find.text(en.recipesEmpty), findsOneWidget);
  });
}
