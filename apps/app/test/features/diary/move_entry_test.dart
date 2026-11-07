import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/edit_entry_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/entry_tile.dart';
import 'package:smartnutri_ai/features/diary/presentation/move_entry_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/slot_section.dart';

import 'diary_harness.dart';

void main() {
  testWidgets('move sends only meal_slot_id', (t) async {
    final env = DiaryEnv(day: 'day_complete_under');
    env.slotsFromDay();
    await pumpDiary(t, env);
    final source = env.diary.day.slots.firstWhere((s) => s.entries.isNotEmpty);
    final entry = source.entries.first;
    final tile = find.byKey(EntryTile.tileKey(entry.id));
    await t.ensureVisible(tile);
    await t.pumpAndSettle();
    await t.tap(tile);
    await t.pumpAndSettle();
    await t.tap(find.byKey(EditEntrySheet.moveKey));
    await t.pumpAndSettle();
    final target = env.slots.items.firstWhere((s) => s.id != source.slotId);
    await t.tap(find.byKey(SlotChoiceList.optionKey(target.id)));
    await t.pumpAndSettle();
    final (id, patch) = env.meals.updated.single;
    expect(id, entry.id);
    expect(patch.mealSlotId, target.id);
    expect(patch.grams, isNull);
    expect(patch.servings, isNull);
    expect(patch.eatenAt, isNull);
    expect(patch.quick, isNull);
    // Both sheets close and the day reloads.
    expect(find.byKey(EditEntrySheet.moveKey), findsNothing);
    expect(env.diary.dayDates.length, greaterThan(1));
  });

  testWidgets('removed slot shows badge and move', (t) async {
    final env = DiaryEnv(day: 'day_archived_slot');
    env.slotsFromDay();
    await pumpDiary(t, env);
    final removed = env.diary.day.slots.firstWhere(
      (s) => s.archived && s.entries.isNotEmpty,
    );
    expect(find.byKey(SlotSection.removedKey(removed.slotId)), findsOneWidget);
    final entry = removed.entries.first;
    final move = find.byKey(EntryTile.moveKey(entry.id));
    await t.ensureVisible(move);
    await t.pumpAndSettle();
    await t.tap(move);
    await t.pumpAndSettle();
    // Only active meals are offered.
    expect(find.byKey(SlotChoiceList.optionKey(removed.slotId)), findsNothing);
    final target = env.slots.items.first;
    await t.tap(find.byKey(SlotChoiceList.optionKey(target.id)));
    await t.pumpAndSettle();
    expect(env.meals.updated.single.$2.mealSlotId, target.id);
  });

  testWidgets('active slots offer no move on the row', (t) async {
    final env = DiaryEnv(day: 'day_complete_under');
    await pumpDiary(t, env);
    final entry = env.diary.day.slots.expand((s) => s.entries).first;
    expect(find.byKey(EntryTile.moveKey(entry.id)), findsNothing);
  });
}
