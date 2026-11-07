import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/diary/presentation/pending_entries.dart';
import 'package:smartnutri_ai/features/diary/presentation/slot_section.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_diary.dart';
import '../../support/fake_meals.dart';
import '../../support/fixtures.dart';
import 'diary_harness.dart';

Future<void> _open(WidgetTester t, [Key key = DiaryScreen.addFabKey]) async {
  await t.tap(find.byKey(key));
  await t.pumpAndSettle();
}

DiaryEnv _env({String day = 'day_complete_under'}) {
  final env = DiaryEnv(day: day)..diary.recents = [recentItem()];
  env.slotsFromDay();
  return env;
}

void main() {
  testWidgets('recent tap logs last grams into the slot', (t) async {
    final env = _env();
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.productId, 'p-oats');
    expect(sent.grams, 40);
    // The API's suggestion (the first slot here) is preselected.
    expect(sent.mealSlotId, env.slots.items.first.id);
    expect(sent.localDate, isNull);
    expect(sent.eatenAt, isNotNull);
    expect(find.byKey(AddFoodSheet.recentKey('p-oats')), findsNothing);
  });

  testWidgets('past day sends local_date not eaten_at', (t) async {
    final env = _env();
    env.diary.dayFor = (date) {
      final j = diaryJson('day_complete_under');
      if (date != null) j['date'] = '2026-11-06';
      return DiaryDayOut.fromJson(
        jsonDecode(jsonEncode(j)) as Map<String, Object?>,
      );
    };
    await pumpDiary(t, env, initial: '/diary?date=2026-11-06');
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    final sent = env.meals.logged.single;
    expect(sent.localDate, DateTime.utc(2026, 11, 6));
    expect(sent.eatenAt, isNull);
  });

  testWidgets('slot chips preselect the tapped slot', (t) async {
    final env = _env();
    await pumpDiary(t, env);
    final lunch = env.diary.day.slots[1];
    await t.ensureVisible(find.byKey(SlotSection.addKey(lunch.slotId)));
    await t.pumpAndSettle();
    await _open(t, SlotSection.addKey(lunch.slotId));
    final chip = t.widget<ChoiceChip>(
      find.byKey(AddFoodSheet.chipKey(lunch.slotId)),
    );
    expect(chip.selected, isTrue);
    expect(env.diary.recentSlots.last, lunch.slotId);
    // Another chip changes the slot that is sent.
    final dinner = env.diary.day.slots[3];
    await t.tap(find.byKey(AddFoodSheet.chipKey(dinner.slotId)));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    expect(env.meals.logged.single.mealSlotId, dinner.slotId);
  });

  testWidgets('no slot list hides chips and sends no slot', (t) async {
    final env = _env();
    env.slots.error = networkError();
    await pumpDiary(t, env);
    await _open(t);
    expect(find.byType(ChoiceChip), findsNWidgets(5)); // segments only
    expect(
      find.byKey(AddFoodSheet.chipKey(env.diary.day.slots.first.slotId)),
      findsNothing,
    );
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    expect(env.meals.logged.single.mealSlotId, isNull);
  });

  testWidgets('queued entry shows waiting to sync without numbers', (t) async {
    final env = _env();
    env.meals.logResponses.add(networkError());
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    final row = (await env.queue.pending()).single;
    final tile = find.byKey(PendingEntryTile.tileKey(row.clientId));
    await t.ensureVisible(tile);
    await t.pumpAndSettle();
    expect(tile, findsOneWidget);
    final shown = texts(t, root: tile);
    expect(shown, contains('Masala Oats'));
    expect(shown, contains(en.diaryWaitingSync));
    expect(shown.any((s) => RegExp(r'\d').hasMatch(s)), isFalse);
  });

  testWidgets('logged entry sends diary_entry_added with method only', (
    t,
  ) async {
    final env = _env();
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.recentKey('p-oats')));
    await t.pumpAndSettle();
    final added = env.events.where((e) => e.$1 == 'diary_entry_added');
    expect(added.single.$2, {'method': 'recent'});
  });

  testWidgets('search, barcode and label hand over with the slot and day', (
    t,
  ) async {
    final env = _env();
    await pumpDiary(t, env);
    await _open(t);
    await t.tap(find.byKey(AddFoodSheet.segmentKey('search')));
    await t.pumpAndSettle();
    // The existing search screen opens.
    expect(find.text(en.searchTitle), findsWidgets);
    expect(env.meals.logged, isEmpty);
  });
}
