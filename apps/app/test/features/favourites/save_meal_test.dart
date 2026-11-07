import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/slot_section.dart';
import 'package:smartnutri_ai/features/favourites/presentation/save_meal_favourite_sheet.dart';

import '../../support/fake_meals.dart';
import '../diary/diary_harness.dart';

Future<DiaryEnv> _open(WidgetTester t, {String locale = 'en'}) async {
  final env = DiaryEnv();
  env.slotsFromDay();
  await pumpDiary(t, env, locale: locale);
  final slot = env.diary.day.slots.first;
  await t.ensureVisible(find.byKey(SlotSection.menuKey(slot.slotId)));
  await t.tap(find.byKey(SlotSection.menuKey(slot.slotId)));
  await t.pumpAndSettle();
  await t.tap(find.text(en.favouritesSaveMeal));
  await t.pumpAndSettle();
  return env;
}

void main() {
  for (final name in ['मेरा नाश्ता ', 'माझा नाश्ता  ']) {
    testWidgets('name kept exactly as typed in hi and mr: "$name"', (t) async {
      final env = await _open(t);
      await t.enterText(find.byKey(SaveMealFavouriteSheet.nameKey), name);
      await t.pump();
      await t.tap(find.byKey(SaveMealFavouriteSheet.saveKey));
      await t.pumpAndSettle();
      final sent = env.favourites.meals.single;
      expect(sent.name, name);
      expect(sent.fromSlotId, env.diary.day.slots.first.slotId);
      expect(sent.clientId, isNotEmpty);
    });
  }

  testWidgets('blank name cannot be saved', (t) async {
    final env = await _open(t);
    await t.enterText(find.byKey(SaveMealFavouriteSheet.nameKey), '   ');
    await t.pump();
    await t.tap(find.byKey(SaveMealFavouriteSheet.saveKey));
    await t.pumpAndSettle();
    expect(env.favourites.meals, isEmpty);
  });

  testWidgets('empty slot shows copy_source_empty message', (t) async {
    final env = DiaryEnv();
    env.slotsFromDay();
    env.favourites.errors['addMeal'] = [apiError(422, 'copy_source_empty')];
    await pumpDiary(t, env);
    final slot = env.diary.day.slots.first;
    await t.ensureVisible(find.byKey(SlotSection.menuKey(slot.slotId)));
    await t.tap(find.byKey(SlotSection.menuKey(slot.slotId)));
    await t.pumpAndSettle();
    await t.tap(find.text(en.favouritesSaveMeal));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(SaveMealFavouriteSheet.nameKey), 'Mine');
    await t.pump();
    await t.tap(find.byKey(SaveMealFavouriteSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorCopySourceEmpty), findsOneWidget);
  });

  testWidgets('name never in analytics', (t) async {
    final env = await _open(t);
    await t.enterText(find.byKey(SaveMealFavouriteSheet.nameKey), 'Secret mix');
    await t.pump();
    await t.tap(find.byKey(SaveMealFavouriteSheet.saveKey));
    await t.pumpAndSettle();
    expect(env.favourites.meals, hasLength(1));
    expect(env.events.toString(), isNot(contains('Secret')));
  });
}
