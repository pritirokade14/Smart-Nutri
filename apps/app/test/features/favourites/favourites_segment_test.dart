import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/favourites/presentation/favourites_segment.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_favourites.dart';
import '../../support/fake_meals.dart';
import '../diary/diary_harness.dart';

DiaryEnv _env({String day = 'day_complete_under', List<FavouriteOut>? favs}) {
  final env = DiaryEnv(
    day: day,
    favourites: FakeFavouritesClient(items: favs),
  );
  env.slotsFromDay();
  return env;
}

Future<void> _openFavourites(WidgetTester t) async {
  await t.tap(find.byKey(DiaryScreen.addFabKey));
  await t.pumpAndSettle();
  await t.tap(find.byKey(AddFoodSheet.segmentKey('favourites')));
  await t.pumpAndSettle();
}

final _meal = favouriteOut(
  id: 'fm',
  name: 'मेरा नाश्ता',
  kind: FavouriteOutKind.meal,
  itemCount: 3,
);

void main() {
  testWidgets('food favourite tap logs default portion with method favourite', (
    t,
  ) async {
    final env = _env(
      favs: [
        favouriteOut(attributions: ['attribution.usda_fdc']),
      ],
    );
    await pumpDiary(t, env);
    await _openFavourites(t);
    expect(find.text(en.attributionUsdaFdc), findsOneWidget);
    await t.tap(find.byKey(FavouritesSegment.rowKey('fav-1')));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.productId, 'p-oats');
    expect(sent.quantity, 40);
    expect(sent.unit?.json, 'g');
    expect(env.events.where((e) => e.$1 == 'diary_entry_added').single.$2, {
      'method': 'favourite',
    });
  });

  testWidgets('food favourite queues offline', (t) async {
    final env = _env(favs: [favouriteOut()]);
    env.meals.logResponses.add(networkError());
    await pumpDiary(t, env);
    await _openFavourites(t);
    await t.tap(find.byKey(FavouritesSegment.rowKey('fav-1')));
    await t.pumpAndSettle();
    final row = (await env.queue.pending()).single;
    expect(row.productId, 'p-oats');
    expect(find.text(en.mealsQueuedOffline), findsWidgets);
  });

  testWidgets('meal favourite log again sends client_id and toasts count only '
      'under hide_all', (t) async {
    final env = _env(day: 'day_hide_all', favs: [_meal]);
    await pumpDiary(t, env);
    await _openFavourites(t);
    expect(find.text('मेरा नाश्ता'), findsOneWidget);
    expect(find.text(en.favouritesMealItems(3)), findsOneWidget);
    await t.tap(find.byKey(FavouritesSegment.logAgainKey('fm')));
    await t.pumpAndSettle();
    final (id, body) = env.favourites.logs.single;
    expect(id, 'fm');
    expect(body.clientId, isNotEmpty);
    expect(body.mealSlotId, env.slots.items.first.id);
    expect(find.text(en.favouritesMealItems(2)), findsOneWidget);
    expect(find.textContaining('kcal'), findsNothing);
    // Name and counts only: nothing but the method reaches analytics.
    for (final e in env.events) {
      expect(e.$2.values.every((v) => v == 'favourite' || v is! String), true);
    }
  });

  testWidgets('retry reuses client_id', (t) async {
    final env = _env(favs: [_meal]);
    env.favourites.errors['log'] = [networkError()];
    await pumpDiary(t, env);
    await _openFavourites(t);
    await t.tap(find.byKey(FavouritesSegment.logAgainKey('fm')));
    await t.pumpAndSettle();
    expect(find.text(en.errorNetwork), findsOneWidget);
    await t.tap(find.byKey(FavouritesSegment.logAgainKey('fm')));
    await t.pumpAndSettle();
    final ids = [for (final l in env.favourites.logs) l.$2.clientId];
    expect(ids.length, 2);
    expect(ids[0], ids[1]);
  });

  testWidgets('food_retired shows its message', (t) async {
    final env = _env(favs: [_meal]);
    env.favourites.errors['log'] = [apiError(422, 'food_retired')];
    await pumpDiary(t, env);
    await _openFavourites(t);
    await t.tap(find.byKey(FavouritesSegment.logAgainKey('fm')));
    await t.pumpAndSettle();
    expect(find.text(en.errorFoodRetired), findsOneWidget);
  });

  testWidgets('empty state', (t) async {
    final env = _env();
    await pumpDiary(t, env);
    await _openFavourites(t);
    expect(find.byKey(FavouritesSegment.emptyKey), findsOneWidget);
    expect(find.text(en.favouritesEmpty), findsOneWidget);
  });

  testWidgets('saved meal items show ml for an ml item, g otherwise', (
    t,
  ) async {
    final env = _env(
      favs: [
        favouriteOut(
          id: 'fm2',
          name: 'Breakfast',
          kind: FavouriteOutKind.meal,
          itemCount: 2,
          items: const [
            FavouriteItemOut(
              grams: 200,
              name: 'Milk',
              quantity: 1,
              sourceKind: FavouriteItemOutSourceKind.food,
              unit: 'glass',
              basis: FavouriteItemOutBasis.ml,
            ),
            FavouriteItemOut(
              grams: 40,
              name: 'Oats',
              quantity: 40,
              sourceKind: FavouriteItemOutSourceKind.food,
              unit: 'g',
            ),
          ],
        ),
      ],
    );
    await pumpDiary(t, env);
    await _openFavourites(t);
    expect(find.textContaining('200 ml'), findsOneWidget);
    expect(find.textContaining('200 g'), findsNothing);
    expect(find.textContaining('40 g'), findsOneWidget);
  });

  testWidgets('food favourite without a default portion opens the picker', (
    t,
  ) async {
    final env = _env(favs: [favouriteOut(quantity: null, unit: null)]);
    await pumpDiary(t, env);
    await _openFavourites(t);
    await t.tap(find.byKey(FavouritesSegment.rowKey('fav-1')));
    await t.pumpAndSettle();
    expect(find.byType(PortionPickerSheet), findsOneWidget);
    expect(env.meals.logged, isEmpty);
    expect(await env.queue.pending(), isEmpty);
  });

  testWidgets('saved meal can be removed and shows its credit', (t) async {
    final env = _env(
      favs: [
        favouriteOut(
          id: 'fm',
          name: 'मेरा नाश्ता',
          kind: FavouriteOutKind.meal,
          itemCount: 3,
          attributions: ['attribution.usda_fdc'],
        ),
      ],
    );
    await pumpDiary(t, env);
    await _openFavourites(t);
    expect(find.text(en.attributionUsdaFdc), findsOneWidget);
    await t.tap(find.byKey(FavouritesSegment.removeKey('fm')));
    await t.pumpAndSettle();
    expect(env.favourites.deleted.single, 'fm');
    expect(find.byKey(FavouritesSegment.emptyKey), findsOneWidget);
  });
}
