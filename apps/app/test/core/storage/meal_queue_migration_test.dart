import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/meals/data/meal_sync.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_draft.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';

import '../../support/fake_meals.dart';

/// The v1 `pending_meals` table, exactly as the shipped app created it.
const _v1Table = '''
CREATE TABLE pending_meals (
  client_id TEXT NOT NULL,
  member_id TEXT NOT NULL,
  product_id TEXT NULL,
  barcode TEXT NULL,
  grams REAL NULL,
  servings REAL NULL,
  eaten_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  PRIMARY KEY (client_id)
)''';

void main() {
  test('queue v1 rows migrate and sync', () async {
    final eaten = DateTime.utc(2026, 11, 3, 8).millisecondsSinceEpoch ~/ 1000;
    final db = MealQueueDatabase(
      NativeDatabase.memory(
        setup: (raw) {
          raw.execute(_v1Table);
          raw.execute(
            "INSERT INTO pending_meals (client_id, member_id, product_id, "
            "grams, eaten_at, attempts) VALUES "
            "('old-1', 'm1', 'p1', 30.0, $eaten, 2)",
          );
          raw.execute('PRAGMA user_version = 1');
        },
      ),
    );
    addTearDown(db.close);
    final queue = DriftMealQueue(db);

    // It opens at v2 with the row intact and the new columns empty.
    final rows = await queue.pending();
    expect(rows, hasLength(1));
    final row = rows.single;
    expect(row.clientId, 'old-1');
    expect(row.attempts, 2);
    expect(row.mealSlotId, isNull);
    expect(row.localDate, isNull);
    expect(row.quickEnergyKcal, isNull);
    expect(row.displayName, isNull);

    // It syncs with no slot, no local_date and its own eaten_at.
    final body = MealSync.toMealIn(row);
    expect(body.mealSlotId, isNull);
    expect(body.localDate, isNull);
    expect(body.quick, isNull);
    expect(body.eatenAt, DateTime.utc(2026, 11, 3, 8));
    expect(body.grams, 30);
    expect(body.clientId, 'old-1');

    final api = FakeMealsClient();
    final result = await MealSync(api, queue).flush();
    expect(result.sent, 1);
    expect(api.logged.single.clientId, 'old-1');
    expect(await queue.pending(), isEmpty);
  });

  test('a v2 row sends its slot, and local_date instead of eaten_at', () async {
    final db = MealQueueDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final queue = DriftMealQueue(db);
    final api = FakeMealsClient();
    final repo = MealsRepository(api, queue, MealSync(api, queue));
    await repo.log(
      MealDraft(
        memberId: 'm1',
        productId: 'p1',
        grams: 40,
        eatenAt: DateTime.utc(2026, 11, 6, 12),
        mealSlotId: 'slot-lunch',
        localDate: '2026-11-06',
        displayName: 'Oats',
      ),
    );
    final sent = api.logged.single;
    expect(sent.mealSlotId, 'slot-lunch');
    expect(sent.localDate, DateTime.utc(2026, 11, 6));
    expect(sent.eatenAt, isNull);
  });

  test('a quick add queues with its values, blanks as null', () async {
    final db = MealQueueDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final queue = DriftMealQueue(db);
    final api = FakeMealsClient(logResponses: [networkError()]);
    final repo = MealsRepository(api, queue, MealSync(api, queue));
    final result = await repo.log(
      MealDraft(
        memberId: 'm1',
        eatenAt: DateTime.utc(2026, 11, 7, 9),
        quickName: 'Tea',
        quickEnergyKcal: 80,
        displayName: 'Tea',
      ),
    );
    expect(result, isA<MealQueued>());
    final row = (await queue.pending()).single;
    expect(row.quickEnergyKcal, 80);
    expect(row.quickProteinG, isNull);
    expect(row.quickFatG, isNull);
    final body = MealSync.toMealIn(row);
    expect(body.quick!.energyKcal, 80);
    expect(body.quick!.proteinG, isNull);
    expect(body.grams, isNull);
    expect(body.productId, isNull);
  });
}
