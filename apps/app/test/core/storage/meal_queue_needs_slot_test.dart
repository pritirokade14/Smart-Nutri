import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';

PendingMeal _row(String id) => PendingMeal(
  clientId: id,
  memberId: 'm1',
  productId: 'p1',
  grams: 30,
  eatenAt: DateTime.utc(2026, 11, 3, 8),
  attempts: 0,
);

void main() {
  for (final code in [mealSlotArchivedError, mealSlotNotFoundError]) {
    test('$code rows wait for a slot and survive clearFailed', () async {
      final db = MealQueueDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final q = DriftMealQueue(db);
      await q.add(_row('wait'));
      await q.add(_row('bad'));
      await q.markFailed('wait', code);
      await q.markFailed('bad', 'validation_error');

      expect(await q.watchFailedCount().first, 1);
      expect((await q.watchNeedingSlot().first).map((r) => r.clientId), [
        'wait',
      ]);

      await q.clearFailed();
      final left = await q.watchNeedingSlot().first;
      expect(left.map((r) => r.clientId), ['wait']);
      expect(await q.watchFailedCount().first, 0);

      await q.retryWithSlot('wait', 's2');
      final p = await q.pending();
      expect(p.single.clientId, 'wait');
      expect(p.single.mealSlotId, 's2');
    });
  }
}
