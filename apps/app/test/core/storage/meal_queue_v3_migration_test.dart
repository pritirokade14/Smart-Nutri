import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/diary/presentation/pending_entries.dart';
import 'package:smartnutri_ai/features/meals/data/meal_sync.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_draft.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';

/// The v2 `pending_meals` table, exactly as the shipped app created it.
const _v2Table = '''
CREATE TABLE pending_meals (
  client_id TEXT NOT NULL,
  member_id TEXT NOT NULL,
  product_id TEXT NULL,
  barcode TEXT NULL,
  grams REAL NULL,
  servings REAL NULL,
  eaten_at INTEGER NOT NULL,
  meal_slot_id TEXT NULL,
  local_date TEXT NULL,
  quick_name TEXT NULL,
  quick_energy_kcal REAL NULL,
  quick_protein_g REAL NULL,
  quick_fat_g REAL NULL,
  quick_carbs_g REAL NULL,
  quick_fibre_g REAL NULL,
  display_name TEXT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  PRIMARY KEY (client_id)
)''';

void main() {
  test('v2 rows migrate and sync', () async {
    final eaten = DateTime.utc(2026, 11, 5, 8).millisecondsSinceEpoch ~/ 1000;
    final db = MealQueueDatabase(
      NativeDatabase.memory(
        setup: (raw) {
          raw.execute(_v2Table);
          raw.execute(
            "INSERT INTO pending_meals (client_id, member_id, product_id, "
            "grams, eaten_at, meal_slot_id, display_name) VALUES "
            "('old-2', 'm1', 'p1', 30.0, $eaten, 'slot-1', 'Oats')",
          );
          raw.execute('PRAGMA user_version = 2');
        },
      ),
    );
    addTearDown(db.close);
    final queue = DriftMealQueue(db);

    final row = (await queue.pending()).single;
    expect(row.foodId, isNull);
    expect(row.quantity, isNull);
    expect(row.unit, isNull);
    final body = MealSync.toMealIn(row);
    expect(body.foodId, isNull);
    expect(body.quantity, isNull);
    expect(body.unit, isNull);
    expect(body.grams, 30);
    expect(body.mealSlotId, 'slot-1');

    final api = FakeMealsClient();
    expect((await MealSync(api, queue).flush()).sent, 1);
    expect(api.logged.single.clientId, 'old-2');
  });

  test(
    'a queued food row keeps food, quantity and unit and syncs them',
    () async {
      final db = MealQueueDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final queue = DriftMealQueue(db);
      final api = FakeMealsClient(logResponses: [networkError()]);
      final repo = MealsRepository(api, queue, MealSync(api, queue));
      final result = await repo.log(
        MealDraft(
          memberId: 'm1',
          foodId: 'f1',
          quantity: 1.5,
          unit: 'katori',
          eatenAt: DateTime.utc(2026, 11, 7, 9),
          displayName: 'Dal',
        ),
      );
      expect(result, isA<MealQueued>());
      final row = (await queue.pending()).single;
      expect(row.foodId, 'f1');
      expect(row.quantity, 1.5);
      expect(row.unit, 'katori');
      expect(row.grams, isNull);
      final body = MealSync.toMealIn(row);
      expect(body.foodId, 'f1');
      expect(body.quantity, 1.5);
      expect(body.unit, MealInUnit.katori);
      expect(body.grams, isNull);
      expect(body.servings, isNull);
    },
  );

  testWidgets('queued food row has no numbers', (t) async {
    final row = PendingMeal(
      clientId: 'c1',
      memberId: 'm1',
      foodId: 'f1',
      quantity: 2,
      unit: 'katori',
      eatenAt: DateTime.utc(2026, 11, 7, 9),
      attempts: 0,
      displayName: 'Dal tadka',
    );
    await t.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: PendingEntryTile(row: row)),
      ),
    );
    final en = lookupAppLocalizations(const Locale('en'));
    expect(find.text('Dal tadka'), findsOneWidget);
    expect(find.text(en.diaryWaitingSync), findsOneWidget);
    final shown = [
      for (final w in t.widgetList<Text>(find.byType(Text))) w.data ?? '',
    ].join(' ');
    expect(RegExp(r'\d').hasMatch(shown), isFalse);
  });
}
