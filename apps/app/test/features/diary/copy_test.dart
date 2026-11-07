import 'package:flutter/widgets.dart' show Key;
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/copy_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/day_menu.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import 'diary_harness.dart';

Future<void> _copyYesterday(WidgetTester t) async {
  await t.tap(find.byKey(DayMenu.menuKey));
  await t.pumpAndSettle();
  await t.tap(find.byKey(DayMenu.copyYesterdayKey));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('copy yesterday sends whole-day copy', (t) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    await _copyYesterday(t);
    final c = env.meals.copied.single;
    expect(c.fromDate, DateTime.utc(2026, 11, 6));
    expect(c.toDate, DateTime.utc(2026, 11, 7));
    expect(c.fromSlotId, isNull);
    expect(c.toSlotId, isNull);
    expect(c.clientId, isNotEmpty);
    expect(find.text(en.diaryCopied(1)), findsOneWidget);
    expect(env.events.where((e) => e.$1 == 'diary_entry_added').single.$2, {
      'method': 'copy',
    });
  });

  testWidgets('retry reuses client_id', (t) async {
    final env = DiaryEnv();
    env.meals.copyResponses.add(networkError());
    await pumpDiary(t, env);
    await _copyYesterday(t);
    expect(find.text(en.errorNetwork), findsOneWidget);
    await t.tap(find.byKey(CopySheet.retryKey));
    await t.pumpAndSettle();
    expect(env.meals.copied.length, 2);
    expect(env.meals.copied[0].clientId, env.meals.copied[1].clientId);
    expect(find.text(en.diaryCopied(1)), findsOneWidget);
  });

  testWidgets('a new action gets a new client_id', (t) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    await _copyYesterday(t);
    await _copyYesterday(t);
    expect(env.meals.copied.length, 2);
    expect(env.meals.copied[0].clientId, isNot(env.meals.copied[1].clientId));
  });

  testWidgets('copied toast shows count only under hide_all', (t) async {
    final env = DiaryEnv(day: 'day_hide_all');
    env.meals.copyResponses.add(
      CopyOut(
        created: [
          mealOut(id: 'a'),
          mealOut(id: 'b'),
        ],
      ),
    );
    await pumpDiary(t, env);
    await _copyYesterday(t);
    expect(find.text(en.diaryCopied(2)), findsOneWidget);
    expect(find.textContaining('kcal'), findsNothing);
  });

  for (final (code, status) in [
    ('copy_source_empty', 422),
    ('date_too_old', 422),
  ]) {
    testWidgets('copy errors map to messages: $code', (t) async {
      final env = DiaryEnv();
      env.meals.copyResponses.add(apiError(status, code));
      await pumpDiary(t, env);
      await _copyYesterday(t);
      expect(
        find.text(
          code == 'copy_source_empty'
              ? en.errorCopySourceEmpty
              : en.errorDateTooOld,
        ),
        findsOneWidget,
      );
    });
  }

  testWidgets('copy this meal asks for a day and a meal', (t) async {
    final env = DiaryEnv();
    env.slotsFromDay();
    await pumpDiary(t, env);
    final lunch = env.diary.day.slots[1];
    final menu = find.byKey(Key('diary-slot-menu-${lunch.slotId}'));
    await t.ensureVisible(menu);
    await t.pumpAndSettle();
    await t.tap(menu);
    await t.pumpAndSettle();
    await t.tap(find.text(en.diaryCopyMeal).last);
    await t.pumpAndSettle();
    await t.tap(find.byKey(CopySheet.slotKey(env.diary.day.slots[3].slotId)));
    await t.pumpAndSettle();
    await t.tap(find.byKey(CopySheet.copyKey));
    await t.pumpAndSettle();
    final c = env.meals.copied.single;
    expect(c.fromSlotId, lunch.slotId);
    expect(c.toSlotId, env.diary.day.slots[3].slotId);
  });
}
