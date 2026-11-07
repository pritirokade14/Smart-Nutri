import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/favourites/presentation/favourite_star.dart';
import 'package:smartnutri_ai/features/foods/presentation/food_search_view.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_diary.dart';
import '../../support/fake_foods.dart';
import '../../support/fake_meals.dart';
import '../diary/diary_harness.dart';

DiaryEnv _env({String? favouriteId, FakeFoodsClient? foods}) {
  final env = DiaryEnv(foods: foods)
    ..diary.recents = [
      RecentItem.fromJson({
        ...recentItem().toJson(),
        'favourite_id': favouriteId,
      }),
    ];
  env.slotsFromDay();
  return env;
}

Future<void> _open(WidgetTester t) async {
  await t.tap(find.byKey(DiaryScreen.addFabKey));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('star toggles add and delete', (t) async {
    final env = _env();
    await pumpDiary(t, env);
    await _open(t);
    final star = find.byKey(FavouriteStar.starKey('product-p-oats'));
    await t.tap(star);
    await t.pumpAndSettle();
    final add = env.favourites.added.single;
    expect(add.productId, 'p-oats');
    expect(find.text(en.favouritesAdded), findsOneWidget);
    // Starring did not log anything.
    expect(env.meals.logged, isEmpty);
    // Let the toast go: it covers the star.
    await t.pump(const Duration(seconds: 6));
    await t.pumpAndSettle();
    await t.tap(star);
    await t.pumpAndSettle();
    expect(env.favourites.deleted.single, 'fav-new-1');
  });

  testWidgets('a starred recent deletes by favourite_id', (t) async {
    final env = _env(favouriteId: 'fav-9');
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(FavouriteStar.starKey('product-p-oats')));
    await t.pumpAndSettle();
    expect(env.favourites.deleted.single, 'fav-9');
    expect(env.favourites.added, isEmpty);
  });

  testWidgets('limit error shows message', (t) async {
    final env = _env();
    env.favourites.errors['add'] = [apiError(409, 'favourite_limit')];
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(FavouriteStar.starKey('product-p-oats')));
    await t.pumpAndSettle();
    expect(find.text(en.errorFavouriteLimit), findsOneWidget);
  });

  testWidgets('food_retired on star shows its message', (t) async {
    final env = _env();
    env.favourites.errors['add'] = [apiError(422, 'food_retired')];
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(FavouriteStar.starKey('product-p-oats')));
    await t.pumpAndSettle();
    expect(find.text(en.errorFoodRetired), findsOneWidget);
  });

  testWidgets('picker toggle stars with the chosen portion after logging', (
    t,
  ) async {
    final foods = FakeFoodsClient(
      search: FoodSearchOut(
        failedSources: const [],
        items: [foodHit('f1', 'Toor dal, cooked')],
        partial: false,
      ),
      details: {'f1': foodDetail()},
    );
    final env = _env(foods: foods);
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.segmentKey('search')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(FoodSearchView.fieldKey), 'dal');
    await t.pump(FoodSearchView.debounce);
    await t.pumpAndSettle();
    await t.tap(find.byKey(FoodSearchView.hitKey(foodHit('f1', 'x'))));
    await t.pumpAndSettle();
    await t.tap(find.byKey(PortionPickerSheet.favouriteKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    expect(env.meals.logged.single.foodId, 'f1');
    final add = env.favourites.added.single;
    expect(add.foodId, 'f1');
    expect(add.defaultQuantity, 1);
    expect(add.defaultUnit, isNotNull);
  });
}
