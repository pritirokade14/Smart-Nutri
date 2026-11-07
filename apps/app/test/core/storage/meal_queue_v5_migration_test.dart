import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';

const _v4Table = '''
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
  custom_food_id TEXT NULL,
  recipe_id TEXT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  PRIMARY KEY (client_id)
)''';

void main() {
  test('v4 opens at v5 with empty weigh-ins', () async {
    final eaten = DateTime.utc(2026, 11, 6, 8).millisecondsSinceEpoch ~/ 1000;
    final db = MealQueueDatabase(
      NativeDatabase.memory(
        setup: (raw) {
          raw.execute(_v4Table);
          raw.execute(
            "INSERT INTO pending_meals (client_id, member_id, food_id, "
            "eaten_at) VALUES ('old-4', 'm1', 'f1', $eaten)",
          );
          raw.execute('PRAGMA user_version = 4');
        },
      ),
    );
    addTearDown(db.close);
    final queue = DriftMealQueue(db);

    expect((await queue.pending()).single.clientId, 'old-4');
    expect(await queue.pendingWeighIns(), isEmpty);
    await queue.addWeighIn(
      PendingWeighIn(
        clientId: 'w1',
        localDate: '2026-11-07',
        weightKg: 70.5,
        confirmUnusual: false,
        status: WeighInStatus.pending,
        attempts: 0,
      ),
    );
    expect((await queue.pendingWeighIns()).single.weightKg, 70.5);
  });

  test('a second weigh-in for the same day replaces the first', () async {
    final db = MealQueueDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final queue = DriftMealQueue(db);
    for (final (id, kg) in [('a', 70.0), ('b', 71.0)]) {
      await queue.addWeighIn(
        PendingWeighIn(
          clientId: id,
          localDate: '2026-11-07',
          weightKg: kg,
          confirmUnusual: false,
          status: WeighInStatus.pending,
          attempts: 0,
        ),
      );
    }
    final rows = await queue.pendingWeighIns();
    expect(rows.single.clientId, 'b');
    await queue.clearAll();
    expect(await queue.pendingWeighIns(), isEmpty);
  });
}
