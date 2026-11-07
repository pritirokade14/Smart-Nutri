import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/foods/presentation/food_search_view.dart';
import 'package:smartnutri_ai/features/foods/presentation/portion_picker_sheet.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_foods.dart';
import '../diary/diary_harness.dart' hide en;
import 'foods_harness.dart';

FoodSearchOut _out(List<FoodHit> items, {bool partial = false}) =>
    FoodSearchOut(
      failedSources: partial ? const ['off'] : const [],
      items: items,
      partial: partial,
    );

final _roti = foodHit(
  'p1',
  'Whole wheat roti',
  kind: FoodHitKind.product,
  group: FoodHitGroup.packaged,
  attributions: const [],
);
final _dal = foodHit('f1', 'Toor dal, cooked');
final _tadka = foodHit(
  'f2',
  'Dal tadka',
  isDish: true,
  attributions: const ['attribution.smartnutri_recipe', 'attribution.usda_fdc'],
);

Future<void> _search(WidgetTester t, String q) async {
  await t.enterText(find.byKey(FoodSearchView.fieldKey), q);
  await t.pump(FoodSearchView.debounce);
  await t.pumpAndSettle();
}

Future<FakeFoodsClient> _pump(WidgetTester t, FoodSearchOut out) async {
  final foods = FakeFoodsClient(search: out);
  await pumpOver(t, foods, FoodSearchView(onPick: (_) {}));
  return foods;
}

void main() {
  testWidgets('debounces to one call', (t) async {
    final foods = await _pump(t, _out([_dal]));
    await t.enterText(find.byKey(FoodSearchView.fieldKey), 'da');
    await t.pump(const Duration(milliseconds: 100));
    await t.enterText(find.byKey(FoodSearchView.fieldKey), 'dal');
    await t.pump(FoodSearchView.debounce);
    await t.pumpAndSettle();
    expect(foods.queries, ['dal']);
  });

  testWidgets('groups indian before packaged', (t) async {
    // The API's order: indian group first.
    await _pump(t, _out([_dal, _tadka, _roti]));
    await _search(t, 'dal');
    final indian = t.getTopLeft(find.text(en.foodsGroupIndian));
    final packaged = t.getTopLeft(find.text(en.foodsGroupPackaged));
    expect(indian.dy, lessThan(packaged.dy));
    expect(find.text(en.foodsKindDish), findsOneWidget);
    expect(find.text(en.foodsKindFood), findsOneWidget);
    expect(find.text(en.foodsKindProduct), findsOneWidget);
  });

  testWidgets('partial shows note not empty state', (t) async {
    await _pump(t, _out(const [], partial: true));
    await _search(t, 'dal');
    expect(find.byKey(FoodSearchView.partialKey), findsOneWidget);
    expect(find.text(en.foodsPartialResults), findsOneWidget);
    expect(find.byKey(FoodSearchView.emptyKey), findsNothing);
  });

  testWidgets('empty and not partial shows no results', (t) async {
    await _pump(t, _out(const []));
    await _search(t, 'zzz');
    expect(find.byKey(FoodSearchView.emptyKey), findsOneWidget);
    expect(find.byKey(FoodSearchView.partialKey), findsNothing);
  });

  testWidgets('hits show credit', (t) async {
    await _pump(t, _out([_dal, _tadka]));
    await _search(t, 'dal');
    expect(find.text(en.attributionUsdaFdc), findsNWidgets(2));
    expect(find.text(en.attributionSmartnutriRecipe), findsOneWidget);
  });

  testWidgets('search tap sends diary_entry_added method search only', (
    t,
  ) async {
    final foods = FakeFoodsClient(search: _out([_dal]));
    final env = DiaryEnv(foods: foods);
    env.slotsFromDay();
    await pumpDiary(t, env);
    await t.tap(find.byKey(DiaryScreen.addFabKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.segmentKey('search')));
    await t.pumpAndSettle();
    await _search(t, 'dal');
    await t.tap(find.byKey(FoodSearchView.hitKey(_dal)));
    await t.pumpAndSettle();
    // The picker is open with the API's default unit; save it.
    await t.tap(find.byKey(PortionPickerSheet.fractionKey('2')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();

    final sent = env.meals.logged.single;
    expect(sent.foodId, 'f1');
    expect(sent.quantity, 2);
    expect(sent.unit, MealInUnit.katori);
    expect(sent.grams, isNull);
    final added = env.events.where((e) => e.$1 == 'diary_entry_added');
    expect(added.single.$2, {'method': 'search'});
  });

  testWidgets('a picked packaged hit logs as a product', (t) async {
    final foods = FakeFoodsClient(
      search: _out([_roti]),
      details: {
        'p1': foodDetail(
          id: 'p1',
          name: 'Whole wheat roti',
          kind: FoodDetailOutKind.product,
          defaultUnit: 'roti',
          units: [unitOut('g', 1), unitOut('roti', 68)],
          reviewPending: false,
        ),
      },
    );
    final env = DiaryEnv(foods: foods);
    env.slotsFromDay();
    await pumpDiary(t, env);
    await t.tap(find.byKey(DiaryScreen.addFabKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.segmentKey('search')));
    await t.pumpAndSettle();
    await _search(t, 'roti');
    await t.tap(find.byKey(FoodSearchView.hitKey(_roti)));
    await t.pumpAndSettle();
    expect(find.text('1 roti ≈ 68 g'), findsOneWidget);
    await t.tap(find.byKey(PortionPickerSheet.saveKey));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.productId, 'p1');
    expect(sent.foodId, isNull);
    expect(sent.unit, MealInUnit.roti);
  });
}
