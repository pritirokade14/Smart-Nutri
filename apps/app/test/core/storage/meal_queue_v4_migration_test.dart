import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/meals/data/meal_sync.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_draft.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';

/// The v3 `pending_meals` table, exactly as slice 3 created it.
const _v3Table = '''
CREATE TABLE pending_meals (
  client_id TEXT NOT NULL,
  member_id TEXT NOT NULL,
  product_id TEXT NULL,
  barcode TEXT NULL,
  grams REAL NULL,
  servings REAL NULL,
  eaten_at INTEGER NOT NULL,
  meal_slot_id TEXT NULL,
  local_date TEXT NULL,
  quick_name TEXT NULL,
  quick_energy_kcal REAL NULL,
  quick_protein_g REAL NULL,
  quick_fat_g REAL NULL,
  quick_carbs_g REAL NULL,
  quick_fibre_g REAL NULL,
  display_name TEXT NULL,
  food_id TEXT NULL,
  quantity REAL NULL,
  unit TEXT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  PRIMARY KEY (client_id)
)''';

void main() {
  test('v3 rows migrate', () async {
    final eaten = DateTime.utc(2026, 11, 6, 8).millisecondsSinceEpoch ~/ 1000;
    final db = MealQueueDatabase(
      NativeDatabase.memory(
        setup: (raw) {
          raw.execute(_v3Table);
          raw.execute(
            "INSERT INTO pending_meals (client_id, member_id, food_id, "
            "quantity, unit, eaten_at, display_name) VALUES "
            "('old-3', 'm1', 'f1', 2.0, 'katori', $eaten, 'Dal')",
          );
          raw.execute('PRAGMA user_version = 3');
        },
      ),
    );
    addTearDown(db.close);
    final queue = DriftMealQueue(db);

    final row = (await queue.pending()).single;
    expect(row.foodId, 'f1');
    expect(row.customFoodId, isNull);
    expect(row.recipeId, isNull);
    final api = FakeMealsClient();
    expect((await MealSync(api, queue).flush()).sent, 1);
    final body = api.logged.single;
    expect(body.clientId, 'old-3');
    expect(body.foodId, 'f1');
    expect(body.customFoodId, isNull);
    expect(body.recipeId, isNull);
  });

  test('queued recipe entry syncs with recipe_id', () async {
    final db = MealQueueDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final queue = DriftMealQueue(db);
    final api = FakeMealsClient(logResponses: [networkError()]);
    final repo = MealsRepository(api, queue, MealSync(api, queue));
    final result = await repo.log(
      MealDraft(
        memberId: 'm1',
        recipeId: 'r1',
        quantity: 1,
        unit: 'serving',
        eatenAt: DateTime.utc(2026, 11, 7, 9),
        displayName: 'Dal',
      ),
    );
    expect(result, isA<MealQueued>());
    final row = (await queue.pending()).single;
    expect(row.recipeId, 'r1');
    expect(row.customFoodId, isNull);
    final body = MealSync.toMealIn(row);
    expect(body.recipeId, 'r1');
    expect(body.foodId, isNull);
    expect(body.unit, MealInUnit.serving);
    expect((await MealSync(api, queue).flush()).sent, 1);
    expect(api.logged.last.recipeId, 'r1');
  });

  test('queued custom food entry syncs with custom_food_id', () async {
    final db = MealQueueDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final queue = DriftMealQueue(db);
    final api = FakeMealsClient(logResponses: [networkError()]);
    final repo = MealsRepository(api, queue, MealSync(api, queue));
    await repo.log(
      MealDraft(
        memberId: 'm1',
        customFoodId: 'c1',
        quantity: 50,
        unit: 'g',
        eatenAt: DateTime.utc(2026, 11, 7, 9),
      ),
    );
    final body = MealSync.toMealIn((await queue.pending()).single);
    expect(body.customFoodId, 'c1');
    expect(body.unit, MealInUnit.g);
  });
}
