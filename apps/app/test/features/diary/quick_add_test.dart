import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/diary/presentation/add_food_sheet.dart';
import 'package:smartnutri_ai/features/diary/presentation/diary_screen.dart';
import 'package:smartnutri_ai/features/diary/presentation/quick_add_form.dart';

import '../../support/fake_meals.dart';
import 'diary_harness.dart';

Future<DiaryEnv> _open(WidgetTester t) async {
  final env = DiaryEnv();
  env.slotsFromDay();
  await pumpDiary(t, env);
  await t.tap(find.byKey(DiaryScreen.addFabKey));
  await t.pumpAndSettle();
  await t.tap(find.byKey(AddFoodSheet.segmentKey('quick')));
  await t.pumpAndSettle();
  return env;
}

Future<void> _save(WidgetTester t) async {
  await t.ensureVisible(find.byKey(QuickAddForm.saveKey));
  await t.pumpAndSettle();
  await t.tap(find.byKey(QuickAddForm.saveKey));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('kcal only sends nulls for blanks', (t) async {
    final env = await _open(t);
    await t.enterText(find.byKey(QuickAddForm.energyKey), '450');
    await _save(t);
    final sent = env.meals.logged.single;
    final q = sent.quick!;
    expect(q.energyKcal, 450);
    expect(q.proteinG, isNull);
    expect(q.fatG, isNull);
    expect(q.carbsG, isNull);
    expect(q.fibreG, isNull);
    expect(q.name, isNull);
    expect(sent.productId, isNull);
    expect(sent.grams, isNull);
    expect(sent.mealSlotId, isNotNull);
  });

  testWidgets('kcal required', (t) async {
    final env = await _open(t);
    await t.enterText(find.byKey(QuickAddForm.proteinKey), '10');
    await _save(t);
    expect(find.text(en.errorQuickAddEnergyRequired), findsOneWidget);
    expect(env.meals.logged, isEmpty);
    expect(await env.queue.pending(), isEmpty);
  });

  testWidgets('the blank note is shown', (t) async {
    await _open(t);
    expect(find.text(en.foodsBlankIsUnknown), findsOneWidget);
  });

  testWidgets('quick add queues offline with its values', (t) async {
    final env = DiaryEnv();
    env.slotsFromDay();
    env.meals.logResponses.add(networkError());
    await pumpDiary(t, env);
    await t.tap(find.byKey(DiaryScreen.addFabKey));
    await t.pumpAndSettle();
    await t.tap(find.byKey(AddFoodSheet.segmentKey('quick')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(QuickAddForm.nameKey), 'Tea');
    await t.enterText(find.byKey(QuickAddForm.energyKey), '80');
    await t.enterText(find.byKey(QuickAddForm.carbsKey), '12.5');
    await _save(t);
    final row = (await env.queue.pending()).single;
    expect(row.quickEnergyKcal, 80);
    expect(row.quickCarbsG, 12.5);
    expect(row.quickProteinG, isNull);
    expect(row.quickName, 'Tea');
    expect(row.displayName, 'Tea');
  });

  testWidgets('quick add name never in analytics', (t) async {
    final env = await _open(t);
    await t.enterText(find.byKey(QuickAddForm.nameKey), 'Secret chai');
    await t.enterText(find.byKey(QuickAddForm.energyKey), '120');
    await _save(t);
    final added = env.events.where((e) => e.$1 == 'diary_entry_added');
    expect(added.single.$2, {'method': 'quick_add'});
    expect(env.events.any((e) => e.toString().contains('Secret')), isFalse);
  });

  testWidgets('API bounds errors show on the form', (t) async {
    final env = await _open(t);
    env.meals.logResponses.add(apiError(422, 'validation_error'));
    await t.enterText(find.byKey(QuickAddForm.energyKey), '9000');
    await _save(t);
    expect(find.text(en.errorValidationError), findsOneWidget);
    expect(await env.queue.pending(), isEmpty);
  });
}
