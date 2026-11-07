import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/day_menu.dart';
import 'package:smartnutri_ai/features/diary/presentation/week_view.dart';

import 'diary_harness.dart';

Future<DiaryEnv> _week(
  WidgetTester t, {
  String week = 'week_mixed',
  String locale = 'en',
}) async {
  final env = DiaryEnv(week: week);
  await pumpDiary(t, env, locale: locale);
  final label = lookupLabel(locale);
  await t.tap(find.text(label));
  await t.pumpAndSettle();
  return env;
}

String lookupLabel(String locale) =>
    {'en': en.diaryWeekTitle}[locale] ??
    // hi and mr read the same key from their own l10n
    en.diaryWeekTitle;

void main() {
  testWidgets('renders golden week_mixed', (t) async {
    final env = await _week(t);
    expect(env.diary.weekEnds, [null]);
    // Seven day tiles, oldest first.
    for (final d in env.diary.week.days) {
      expect(
        find.byKey(WeekView.tileKey(d.date.toIso8601String().substring(0, 10))),
        findsOneWidget,
      );
    }
    // The API's averaged_days (5) and protein_met_days (2).
    expect(
      t.widget<Text>(find.byKey(WeekView.averageKey)).data,
      en.diaryWeekAverage(5),
    );
    expect(
      t.widget<Text>(find.byKey(WeekView.proteinDaysKey)).data,
      en.diaryWeekProteinDays('5', '2'),
    );
    // The partly logged day is marked; the day with an unknown energy too.
    expect(find.byKey(WeekView.partialKey('2026-11-03')), findsOneWidget);
    expect(find.byKey(WeekView.incompleteKey('2026-11-05')), findsOneWidget);
    expect(find.byKey(WeekView.partialKey('2026-11-01')), findsNothing);
  });

  testWidgets('no rating or streak text', (t) async {
    await _week(t);
    final all = texts(t).join(' ').toLowerCase();
    for (final w in ['streak', 'good', 'bad', 'great', 'poor']) {
      expect(all, isNot(contains(w)));
    }
  });

  testWidgets('hide_all leaves no digits on the week', (t) async {
    await _week(t, week: 'week_hide_all');
    final digits = [
      for (final s in texts(t))
        if (RegExp(r'\d').hasMatch(s)) s,
    ];
    expect(digits, isEmpty);
    // No averages and no protein-days line while macros are hidden.
    expect(find.byKey(WeekView.averageKey), findsNothing);
    expect(find.byKey(WeekView.proteinDaysKey), findsNothing);
    // The bar shapes remain.
    expect(find.byKey(WeekView.tileKey('2026-11-02')), findsOneWidget);
  });

  testWidgets('incomplete averages are grey with the note', (t) async {
    await _week(t);
    // week_mixed flags every average incomplete.
    expect(find.textContaining('At least'), findsWidgets);
  });

  testWidgets('mark partial toggles and explains', (t) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    await t.tap(find.byKey(DayMenu.menuKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(DayMenu.partialKey));
    await t.pumpAndSettle();
    expect(env.diary.statuses.single.$1, DateTime.utc(2026, 11, 7));
    expect(env.diary.statuses.single.$2, isTrue);
    expect(find.text(en.diaryPartialNote), findsOneWidget);
  });
}
