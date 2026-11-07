import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/edit_entry_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/entry_tile.dart';

import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import 'diary_harness.dart';

Future<DiaryEnv> _open(
  WidgetTester t, {
  String day = 'day_complete_under',
}) async {
  final env = DiaryEnv(day: day);
  await pumpDiary(t, env);
  final entry = env.diary.day.slots
      .expand((s) => s.entries)
      .firstWhere((e) => e.nutrients.energyKcal != null);
  final tile = find.byKey(EntryTile.tileKey(entry.id));
  await t.ensureVisible(tile);
  await t.pumpAndSettle();
  await t.tap(tile);
  await t.pumpAndSettle();
  return env;
}

void main() {
  testWidgets('edit grams sends only grams', (t) async {
    final env = await _open(t);
    final entry = env.diary.day.slots.first.entries.first;
    await t.tap(find.byKey(EditEntrySheet.plusKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(EditEntrySheet.saveKey));
    await t.pumpAndSettle();
    final (id, patch) = env.meals.updated.single;
    expect(id, entry.id);
    expect(patch.grams, entry.grams! + 10);
    expect(patch.servings, isNull);
    expect(patch.mealSlotId, isNull);
    expect(patch.eatenAt, isNull);
    expect(patch.quick, isNull);
    // The sheet closes and the day reloads.
    expect(find.byKey(EditEntrySheet.saveKey), findsNothing);
    expect(env.diary.dayDates.length, greaterThan(1));
  });

  testWidgets('save is off until the grams change', (t) async {
    await _open(t);
    expect(
      t.widget<ButtonStyleButton>(find.byKey(EditEntrySheet.saveKey)).onPressed,
      isNull,
    );
    await t.tap(find.byKey(EditEntrySheet.minusKey));
    await t.pumpAndSettle();
    expect(
      t.widget<ButtonStyleButton>(find.byKey(EditEntrySheet.saveKey)).onPressed,
      isNotNull,
    );
  });

  testWidgets('remove asks then deletes', (t) async {
    final env = await _open(t);
    final entry = env.diary.day.slots.first.entries.first;
    await t.tap(find.byKey(EditEntrySheet.removeKey));
    await t.pumpAndSettle();
    expect(find.text(en.diaryDeleteConfirm), findsOneWidget);
    expect(env.meals.deleted, isEmpty); // not yet
    await t.tap(find.text(en.diaryDelete).last);
    await t.pumpAndSettle();
    expect(env.meals.deleted, [entry.id]);
    expect(find.byKey(EditEntrySheet.removeKey), findsNothing);
  });

  testWidgets('remove can be cancelled', (t) async {
    final env = await _open(t);
    await t.tap(find.byKey(EditEntrySheet.removeKey));
    await t.pumpAndSettle();
    await t.tap(find.text('Cancel'));
    await t.pumpAndSettle();
    expect(env.meals.deleted, isEmpty);
    expect(find.byKey(EditEntrySheet.saveKey), findsOneWidget);
  });

  testWidgets('offline edit shows the offline message', (t) async {
    final env = await _open(t);
    env.meals.updateError = networkError();
    await t.tap(find.byKey(EditEntrySheet.plusKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(EditEntrySheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorNetwork), findsOneWidget);
    // The sheet stays open so nothing is lost.
    expect(find.byKey(EditEntrySheet.saveKey), findsOneWidget);
  });

  testWidgets('offline remove shows the offline message', (t) async {
    final env = await _open(t);
    env.meals.deleteError = networkError();
    await t.tap(find.byKey(EditEntrySheet.removeKey));
    await t.pumpAndSettle();
    await t.tap(find.text(en.diaryDelete).last);
    await t.pumpAndSettle();
    expect(find.text(en.errorNetwork), findsOneWidget);
  });

  testWidgets('quick add edit sends the quick fields, blanks as null', (
    t,
  ) async {
    final env = DiaryEnv(day: 'day_quick_add_kcal_only');
    await pumpDiary(t, env);
    final entry = env.diary.day.slots.expand((s) => s.entries).single;
    await t.ensureVisible(find.byKey(EntryTile.tileKey(entry.id)));
    await t.tap(find.byKey(EntryTile.tileKey(entry.id)));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(EditEntrySheet.energyKey), '500');
    await t.pumpAndSettle();
    await t.tap(find.byKey(EditEntrySheet.saveKey));
    await t.pumpAndSettle();
    final (_, patch) = env.meals.updated.single;
    expect(patch.grams, isNull);
    expect(patch.quick!.energyKcal, 500);
    expect(patch.quick!.proteinG, isNull);
    expect(patch.quick!.fatG, isNull);
    expect(patch.quick!.carbsG, isNull);
    expect(patch.quick!.fibreG, isNull);
  });

  testWidgets(
    'a quick add with hidden energy can be edited (energy required)',
    (t) async {
      final env = DiaryEnv(day: 'day_quick_add_kcal_only');
      final j =
          jsonDecode(jsonEncode(env.diary.day.toJson()))
              as Map<String, Object?>;
      for (final s in (j['slots'] as List).cast<Map<String, Object?>>()) {
        for (final e in (s['entries'] as List).cast<Map<String, Object?>>()) {
          (e['nutrients'] as Map<String, Object?>)['energy_kcal'] = null;
        }
      }
      env.diary.day = DiaryDayOut.fromJson(j);
      await pumpDiary(t, env);
      final entry = env.diary.day.slots.expand((s) => s.entries).single;
      await t.ensureVisible(find.byKey(EntryTile.tileKey(entry.id)));
      await t.tap(find.byKey(EntryTile.tileKey(entry.id)));
      await t.pumpAndSettle();
      expect(find.byKey(EditEntrySheet.energyKey), findsOneWidget);
      expect(
        t.widget<FilledButton>(find.byKey(EditEntrySheet.saveKey)).onPressed,
        isNull,
      );
      await t.enterText(find.byKey(EditEntrySheet.energyKey), '300');
      await t.pumpAndSettle();
      await t.tap(find.byKey(EditEntrySheet.saveKey));
      await t.pumpAndSettle();
      expect(env.meals.updated.single.$2.quick!.energyKcal, 300);
    },
  );
}
