import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/day_menu.dart';
import 'package:smartnutri_ai/features/diary/presentation/meal_slot_row.dart';
import 'package:smartnutri_ai/features/diary/presentation/meals_screen.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_diary.dart';
import '../../support/fake_meals.dart';
import 'diary_harness.dart';

Future<DiaryEnv> _open(
  WidgetTester t, {
  List<MealSlotOut>? slots,
  String locale = 'en',
}) async {
  final env = DiaryEnv(slots: slots);
  await pumpDiary(t, env, initial: '/diary/meals', locale: locale);
  return env;
}

Future<void> _rename(WidgetTester t, String id, String text) async {
  await t.tap(find.byKey(MealSlotRow.renameKey(id)));
  await t.pumpAndSettle();
  await t.enterText(find.byKey(SlotNameEditor.fieldKey), text);
  await t.pump();
  await t.tap(find.byKey(SlotNameEditor.saveKey));
  await t.pumpAndSettle();
}

MealSlotOut _custom(String id, String label, int pos) =>
    slotOut(id, '', position: pos, customLabel: label);

void main() {
  testWidgets('lists the meals with default names', (t) async {
    await _open(t);
    expect(find.text(en.diarySlotBreakfast), findsOneWidget);
    expect(find.text(en.diarySlotDinner), findsOneWidget);
    expect(find.text(en.diarySlotsManage), findsWidgets);
  });

  testWidgets('reached from the day menu', (t) async {
    final env = DiaryEnv();
    await pumpDiary(t, env);
    await t.tap(find.byKey(DayMenu.menuKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(DayMenu.manageKey));
    await t.pumpAndSettle();
    expect(find.byKey(MealsScreen.listKey), findsOneWidget);
  });

  testWidgets('rename sends custom label exactly as typed', (t) async {
    final env = await _open(t);
    await _rename(t, 'slot-snack', '  Pre-gym  Shake ');
    final (id, body) = env.slots.renamed.single;
    expect(id, 'slot-snack');
    // Trimmed at the ends only; the inside is untouched.
    expect(body.customLabel, 'Pre-gym  Shake');
    expect(body.clearCustomLabel, isFalse);
  });

  testWidgets('reset name sends clear flag', (t) async {
    final custom = MealSlotOut(
      archived: false,
      customLabel: 'My breakfast',
      defaultTimeWindow: null,
      id: 'slot-breakfast',
      isDefault: true,
      labelKey: 'diary.slot.breakfast',
      memberId: 'p1',
      position: 0,
    );
    final env = await _open(t, slots: [custom, ...defaultSlots().skip(1)]);
    await t.tap(find.byKey(MealSlotRow.resetKey('slot-breakfast')));
    await t.pumpAndSettle();
    final (id, body) = env.slots.renamed.single;
    expect(id, 'slot-breakfast');
    expect(body.clearCustomLabel, isTrue);
    expect(body.customLabel, isNull);
  });

  testWidgets('reorder sends every active id', (t) async {
    final env = await _open(t);
    final g = await t.startGesture(
      t.getCenter(find.byKey(MealSlotRow.handleKey('slot-breakfast'))),
    );
    await t.pump(const Duration(milliseconds: 100));
    for (var i = 0; i < 12; i++) {
      await g.moveBy(const Offset(0, 20));
      await t.pump(const Duration(milliseconds: 50));
    }
    await g.up();
    await t.pumpAndSettle();
    final ids = env.slots.reordered.single;
    expect(ids.toSet(), {
      'slot-breakfast',
      'slot-lunch',
      'slot-snack',
      'slot-dinner',
    });
    expect(ids.length, 4);
    expect(ids.first, isNot('slot-breakfast'));
  });

  testWidgets('add creates a meal with the typed name', (t) async {
    final env = await _open(t);
    await t.tap(find.byKey(MealsScreen.addKey));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(SlotNameEditor.fieldKey), 'Post workout');
    await t.pump();
    await t.tap(find.byKey(SlotNameEditor.saveKey));
    await t.pumpAndSettle();
    expect(env.slots.created.single.customLabel, 'Post workout');
    expect(find.text('Post workout'), findsOneWidget);
  });

  testWidgets('add disabled at six with limit message', (t) async {
    await _open(
      t,
      slots: [
        ...defaultSlots(),
        _custom('c1', 'Extra 1', 4),
        _custom('c2', 'Extra 2', 5),
      ],
    );
    expect(
      t.widget<ButtonStyleButton>(find.byKey(MealsScreen.addKey)).onPressed,
      isNull,
    );
    expect(find.text(en.diarySlotsLimit('6')), findsOneWidget);
  });

  testWidgets('limit error from the API shows its message', (t) async {
    final env = await _open(t);
    env.slots.writeError = apiError(422, 'meal_slot_limit_reached');
    await t.tap(find.byKey(MealsScreen.addKey));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(SlotNameEditor.fieldKey), 'Seven');
    await t.pump();
    await t.tap(find.byKey(SlotNameEditor.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorMealSlotLimitReached), findsOneWidget);
  });

  testWidgets('remove shows the note and archives', (t) async {
    final env = await _open(t);
    await t.tap(find.byKey(MealSlotRow.removeKey('slot-snack')));
    await t.pumpAndSettle();
    expect(find.text(en.diarySlotsRemoveNote), findsOneWidget);
    expect(env.slots.archived, isEmpty);
    await t.tap(find.byKey(MealsScreen.removeConfirmKey));
    await t.pumpAndSettle();
    expect(env.slots.archived, ['slot-snack']);
    expect(find.byKey(MealSlotRow.rowKey('slot-snack')), findsNothing);
  });

  testWidgets('last meal cannot be removed', (t) async {
    await _open(t, slots: [defaultSlots().first]);
    expect(
      t
          .widget<IconButton>(
            find.byKey(MealSlotRow.removeKey('slot-breakfast')),
          )
          .onPressed,
      isNull,
    );
    expect(find.text(en.diarySlotsLastActive), findsOneWidget);
  });

  testWidgets('last active error from the API shows its message', (t) async {
    final env = await _open(t);
    env.slots.writeError = apiError(422, 'meal_slot_last_active');
    await t.tap(find.byKey(MealSlotRow.removeKey('slot-snack')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(MealsScreen.removeConfirmKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorMealSlotLastActive), findsOneWidget);
  });

  testWidgets('duplicate name shows inline error', (t) async {
    final env = await _open(t);
    env.slots.writeError = apiError(422, 'meal_slot_label_duplicate');
    await _rename(t, 'slot-snack', 'Lunch');
    expect(find.text(en.errorMealSlotLabelDuplicate), findsOneWidget);
    // Still editing, so the user can change the name.
    expect(find.byKey(SlotNameEditor.fieldKey), findsOneWidget);
  });

  testWidgets('error with retry when the list fails', (t) async {
    final env = DiaryEnv();
    env.slots.error = networkError();
    await pumpDiary(t, env, initial: '/diary/meals');
    expect(find.text(en.errorNetwork), findsOneWidget);
    env.slots.error = null;
    await t.tap(find.text(en.commonRetry));
    await t.pumpAndSettle();
    expect(find.byKey(MealSlotRow.rowKey('slot-lunch')), findsOneWidget);
  });

  for (final (locale, label) in [
    ('en', 'Mom\'s <b>chai</b> 🍵'),
    ('hi', 'सुबह की चाय'),
    ('mr', 'दुपारचा चहा'),
  ]) {
    testWidgets('custom label renders exactly as typed in $locale', (t) async {
      await _open(
        t,
        locale: locale,
        slots: [_custom('c1', label, 0), ...defaultSlots().skip(1)],
      );
      expect(find.text(label), findsOneWidget);
      // The default names follow the language; the custom one does not.
      final l10n = await AppLocalizations.delegate.load(Locale(locale));
      expect(find.text(l10n.diarySlotLunch), findsOneWidget);
    });
  }

  testWidgets('counter counts code points', (t) async {
    final env = await _open(t);
    await t.tap(find.byKey(MealSlotRow.renameKey('slot-snack')));
    await t.pumpAndSettle();
    final field = find.byKey(SlotNameEditor.fieldKey);
    final thirty = List.filled(30, 'क').join();
    await t.enterText(field, thirty);
    await t.pump();
    expect(find.text('30/30'), findsOneWidget);
    // The 31st is blocked: the field keeps the 30.
    await t.enterText(field, [thirty, 'ख'].join());
    await t.pump();
    expect(t.widget<TextField>(field).controller!.text, thirty);
    await t.tap(find.byKey(SlotNameEditor.saveKey));
    await t.pumpAndSettle();
    expect(env.slots.renamed.single.$2.customLabel, thirty);
  });

  testWidgets('no slot label in analytics', (t) async {
    final env = await _open(t);
    const label = 'Secret-label-xyz';
    await _rename(t, 'slot-snack', label);
    await t.tap(find.byKey(MealsScreen.addKey));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(SlotNameEditor.fieldKey), '$label 2');
    await t.pump();
    await t.tap(find.byKey(SlotNameEditor.saveKey));
    await t.pumpAndSettle();
    for (final (name, props) in env.events) {
      expect(name.contains(label), isFalse);
      expect(props.values.join(' ').contains(label), isFalse);
    }
  });
}
