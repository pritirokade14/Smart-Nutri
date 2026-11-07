import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/theme/sn_colors.dart';
import 'package:smartnutri_ai/core/theme/tokens.g.dart';
import 'package:smartnutri_ai/features/diary/presentation/day_header.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_rings.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/diary/presentation/entry_tile.dart';
import 'package:smartnutri_ai/features/diary/presentation/slot_section.dart';
import 'package:smartnutri_ai/features/targets/presentation/eye_toggle.dart';
import 'package:smartnutri_ai/features/targets/presentation/guide_setup_screen.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fixtures.dart';
import 'diary_harness.dart';

Finder get _digitText => find.byWidgetPredicate(
  (w) => w is Text && RegExp(r'\d').hasMatch(w.data ?? ''),
);

String _path(AppHarness h) =>
    h.router.routerDelegate.currentConfiguration.uri.toString();

void main() {
  testWidgets('renders golden day_complete_under', (t) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    final d = env.diary.day;
    // The four default titles come from the label keys.
    for (final s in d.slots) {
      expect(
        find.descendant(
          of: find.byKey(SlotSection.titleKey(s.slotId)),
          matching: find.byType(Text),
        ),
        findsNothing,
      );
    }
    expect(find.text(en.diarySlotBreakfast), findsOneWidget);
    expect(find.text(en.diarySlotLunch), findsOneWidget);
    expect(find.text(en.diarySlotSnack), findsOneWidget);
    expect(find.text(en.diarySlotDinner), findsOneWidget);
    // The energy ring shows remaining.energy_kcal (1258.8) as the API sent it.
    final ring = find.byKey(DiaryRings.ringKey(RingNutrient.energy));
    expect(
      find.descendant(
        of: ring,
        matching: find.text(en.diaryLeft('1258.8 kcal')),
      ),
      findsOneWidget,
    );
    expect(find.text(en.diaryLeft('67.4 g')), findsOneWidget);
    expect(find.byKey(DiaryScreen.pendingReviewKey), findsOneWidget);
    expect(find.text(en.diaryDisclaimer), findsOneWidget);
    expect(env.diary.dayDates, [null]); // today: the API decides the date
  });

  testWidgets('over renders neutral with the absolute value', (t) async {
    await pumpDiary(t, DiaryEnv(day: 'day_over_energy'));
    final over = find.byKey(DiaryRings.overKey(RingNutrient.energy));
    expect(over, findsOneWidget);
    expect(t.widget<Text>(over).data, en.diaryOver('250.4 kcal'));
    final c = SnColors.of(t.element(over));
    final color = t.widget<Text>(over).style?.color;
    expect(color, c.textPrimary);
    expect(color, isNot(SnTokens.verdictAvoid));
    expect(color, isNot(SnTokens.darkVerdictAvoid));
    // Protein is over too (-8.0): absolute value, never "-8".
    expect(find.text(en.diaryOver('8 g')), findsOneWidget);
    expect(find.textContaining('-'), findsNothing);
  });

  testWidgets('incomplete nutrient shows the grey chip, not a number', (
    t,
  ) async {
    await pumpDiary(t, DiaryEnv(day: 'day_incomplete_energy'));
    final chip = find.byKey(DiaryRings.incompleteKey(RingNutrient.energy));
    expect(chip, findsOneWidget);
    expect(
      find.descendant(of: chip, matching: find.text(en.diaryIncomplete)),
      findsOneWidget,
    );
    // No energy figure next to the chip: no "left", no total.
    final ring = find.byKey(DiaryRings.ringKey(RingNutrient.energy));
    expect(
      find.descendant(of: ring, matching: find.textContaining('kcal')),
      findsNothing,
    );
    // Other nutrients still read their remaining.
    expect(find.text(en.diaryLeft('89.5 g')), findsOneWidget);
  });

  testWidgets('quick add with kcal only: unknown macros are chips, not 0', (
    t,
  ) async {
    await pumpDiary(t, DiaryEnv(day: 'day_quick_add_kcal_only'));
    for (final n in [
      RingNutrient.protein,
      RingNutrient.carbs,
      RingNutrient.fat,
    ]) {
      expect(find.byKey(DiaryRings.incompleteKey(n)), findsOneWidget);
    }
    expect(
      find.byKey(DiaryRings.incompleteKey(RingNutrient.energy)),
      findsNothing,
    );
    expect(find.text(en.diaryLeft('2310 kcal')), findsOneWidget);
    expect(find.textContaining(RegExp(r'(^| )0 g')), findsNothing);
  });

  testWidgets('empty day shows nothing logged and remaining equals target', (
    t,
  ) async {
    await pumpDiary(t, DiaryEnv(day: 'day_empty'));
    expect(find.byKey(DiaryScreen.emptyKey), findsOneWidget);
    expect(find.text(en.diaryEmptyDay), findsOneWidget);
    // remaining equals the target the API returned.
    expect(find.text(en.diaryLeft('2760 kcal')), findsOneWidget);
    expect(find.text(en.diaryLeft('112 g')), findsOneWidget);
  });

  testWidgets('no guide shows setup CTA', (t) async {
    await pumpDiary(t, DiaryEnv(day: 'day_no_target'));
    expect(find.byKey(DiaryScreen.noGuideKey), findsOneWidget);
    expect(find.text(en.diaryNoGuide), findsOneWidget);
    // No remaining without a ready guide: the totals show instead.
    expect(find.textContaining(en.diaryLeft('').trim()), findsNothing);
    await t.ensureVisible(find.byKey(DiaryScreen.setupKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(DiaryScreen.setupKey));
    await t.pumpAndSettle();
    expect(find.byType(GuideSetupScreen), findsOneWidget);
  });

  testWidgets('consent_required shows the consent card, not a redirect', (
    t,
  ) async {
    final h = await pumpDiary(t, DiaryEnv(day: 'day_consent_required'));
    expect(find.byKey(DiaryScreen.consentKey), findsOneWidget);
    expect(find.text(en.diaryTargetsConsent), findsOneWidget);
    expect(_path(h), '/diary');
    // The day still loads.
    expect(find.text(en.diarySlotBreakfast), findsOneWidget);
    expect(find.byKey(DiaryScreen.pendingReviewKey), findsNothing);
  });

  testWidgets('hide_all leaves no digits on the day', (t) async {
    await pumpDiary(t, DiaryEnv(day: 'day_hide_all'));
    final shown = texts(t);
    expect(find.byKey(DiaryScreen.hiddenNoteKey), findsOneWidget);
    // Portions (grams) stay by design; nothing else carries a digit apart
    // from the date header and the tab bar.
    final bad = [
      for (final w in t.widgetList<Text>(_digitText))
        if (w.key != DayHeader.dateKeyKey &&
            w.key != EntryTile.portionKey &&
            !RegExp(r'^\d+ g$').hasMatch(w.data!))
          w.data!,
    ];
    expect(bad, isEmpty, reason: shown.join(' | '));
    // The rings still show a fill shape (progress 0.5).
    final bar = find.descendant(
      of: find.byKey(DiaryRings.ringKey(RingNutrient.protein)),
      matching: find.byType(LinearProgressIndicator),
    );
    expect(t.widget<LinearProgressIndicator>(bar).value, 0.5);
    // No kcal anywhere on an entry.
    expect(find.textContaining('kcal'), findsNothing);
  });

  testWidgets('hide_energy hides kcal but keeps macros', (t) async {
    await pumpDiary(t, DiaryEnv(day: 'day_hide_energy'));
    expect(find.textContaining('kcal'), findsNothing);
    expect(find.text(en.diaryLeft('67.4 g')), findsOneWidget);
  });

  testWidgets('next day disabled on today; previous goes to the day before', (
    t,
  ) async {
    final env = DiaryEnv();
    final h = await pumpDiary(t, env);
    expect(
      t.widget<IconButton>(find.byKey(DayHeader.nextKey)).onPressed,
      isNull,
    );
    expect(
      t.widget<Text>(find.byKey(DayHeader.dateKeyKey)).data,
      en.diaryToday,
    );
    await t.tap(find.byKey(DayHeader.prevKey));
    await t.pumpAndSettle();
    expect(_path(h), '/diary?date=2026-11-06');
    expect(env.diary.dayDates.last, DateTime.utc(2026, 11, 6));
  });

  testWidgets('a past day enables next and returns to today', (t) async {
    final env = DiaryEnv();
    env.diary.dayFor = (date) {
      final j = diaryJson('day_complete_under');
      if (date != null) j['date'] = '2026-11-06';
      return DiaryDayOut.fromJson(
        jsonDecode(jsonEncode(j)) as Map<String, Object?>,
      );
    };
    final h = await pumpDiary(t, env, initial: '/diary?date=2026-11-06');
    expect(
      t.widget<IconButton>(find.byKey(DayHeader.nextKey)).onPressed,
      isNotNull,
    );
    await t.tap(find.byKey(DayHeader.nextKey));
    await t.pumpAndSettle();
    expect(_path(h), '/diary');
  });

  testWidgets('consumed view shows totals', (t) async {
    final env = DiaryEnv();
    env.targets.settings = GoalSettingsOut.fromJson({
      ...env.targets.settings!.toJson(),
      'summary_view': 'consumed',
    });
    await pumpDiary(t, env);
    expect(find.text('1501.3 kcal'), findsOneWidget);
    expect(find.text('44.7 g'), findsOneWidget);
    expect(find.textContaining(en.diaryLeft('').trim()), findsNothing);
  });

  testWidgets('the view chip saves summary_view through targets_display_put', (
    t,
  ) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    await t.tap(find.byKey(DiaryRings.toggleKey));
    await t.pumpAndSettle();
    expect(
      env.targets.displays.single.summaryView,
      DisplayInSummaryView.consumed,
    );
  });

  testWidgets('quick add entry shows badge and default name', (t) async {
    final env = DiaryEnv(day: 'day_quick_add_kcal_only');
    final j = diaryJson('day_quick_add_kcal_only');
    for (final s in j['slots']! as List) {
      for (final e in (s as Map)['entries'] as List) {
        (e as Map)['product_name'] = ''; // an unnamed quick add
      }
    }
    env.diary.day = DiaryDayOut.fromJson(
      jsonDecode(jsonEncode(j)) as Map<String, Object?>,
    );
    await pumpDiary(t, env);
    expect(find.byKey(EntryTile.quickBadgeKey), findsOneWidget);
    expect(find.text(en.diaryQuickBadge), findsOneWidget);
    expect(find.text(en.diaryQuickAddName), findsOneWidget);
    // No grams line for a quick add.
    expect(find.byKey(EntryTile.portionKey), findsNothing);
  });

  testWidgets('archived slot with entries is listed', (t) async {
    await pumpDiary(t, DiaryEnv(day: 'day_archived_slot'));
    // The user's own label, exactly as typed.
    expect(find.text('Pre-gym'), findsOneWidget);
  });

  testWidgets('history route redirects to diary', (t) async {
    final h = await pumpDiary(t, DiaryEnv(), initial: '/history');
    expect(_path(h), '/diary');
    expect(find.byType(DiaryScreen), findsOneWidget);
  });

  testWidgets('diary_day_viewed is sent once per open, with no props', (
    t,
  ) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    final viewed = env.events.where((e) => e.$1 == 'diary_day_viewed');
    expect(viewed.length, 1);
    expect(viewed.single.$2, isEmpty);
  });

  testWidgets('the eye toggle shows when settings exist', (t) async {
    await pumpDiary(t, DiaryEnv());
    expect(find.byKey(EyeToggle.buttonKey), findsOneWidget);
  });

  testWidgets('a load error shows retry', (t) async {
    final env = DiaryEnv();
    env.diary.dayError = networkError();
    await pumpDiary(t, env);
    expect(find.text(en.errorNetwork), findsOneWidget);
    env.diary.dayError = null;
    await t.tap(find.text(en.commonRetry));
    await t.pumpAndSettle();
    expect(find.text(en.diarySlotBreakfast), findsOneWidget);
  });
}
