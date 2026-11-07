import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/diary/presentation/move_entry_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/pick_slot_again.dart';
import 'package:smartnutri_ai/features/meals/presentation/meals_providers.dart';

import '../../support/fake_meals.dart';
import 'diary_harness.dart';

void main() {
  testWidgets('archived slot on sync asks to pick again', (t) async {
    // The API refuses the first send: the slot was removed meanwhile.
    final meals = FakeMealsClient(
      logResponses: [apiError(422, 'meal_slot_archived')],
    );
    final env = DiaryEnv(meals: meals);
    env.slotsFromDay();
    await env.queue.add(
      PendingMeal(
        clientId: 'c-pick',
        memberId: 'p1',
        productId: 'prod-1',
        grams: 30,
        eatenAt: DateTime.utc(2026, 11, 7, 8),
        mealSlotId: 'gone-slot',
        displayName: 'Oats',
        attempts: 0,
      ),
    );
    final h = await pumpDiary(t, env);
    // App start flushed once and was refused.
    await h.container.read(mealSyncProvider).flush();
    await t.pumpAndSettle();
    expect(meals.logged.single.clientId, 'c-pick');
    expect(find.text(en.diarySlotsPickAgain), findsOneWidget);
    // Not shown as a plain sync failure.
    expect(find.text(en.mealsSyncFailed), findsNothing);

    await t.tap(find.byKey(PickSlotAgain.buttonKey('c-pick')));
    await t.pumpAndSettle();
    final target = env.slots.items.last;
    await t.tap(find.byKey(SlotChoiceList.optionKey(target.id)));
    await t.pumpAndSettle();

    // Re-sent with the same client_id and the new slot.
    expect(meals.logged.length, 2);
    expect(meals.logged.last.clientId, 'c-pick');
    expect(meals.logged.last.mealSlotId, target.id);
    expect(find.text(en.diarySlotsPickAgain), findsNothing);
    expect(env.queue.rows, isEmpty);
  });
}
