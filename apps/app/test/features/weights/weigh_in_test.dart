import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/weights/data/weight_sync.dart';
import 'package:smartnutri_ai/features/weights/data/weights_repository.dart';
import 'package:smartnutri_ai/features/weights/presentation/progress_view.dart';
import 'package:smartnutri_ai/features/weights/presentation/weigh_in_sheet.dart';
import 'package:smartnutri_ai/features/weights/presentation/weight_list.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_weights.dart';
import 'weights_harness.dart';

Future<void> _enter(WidgetTester t, String kg) async {
  await t.tap(find.byKey(ProgressView.addKey));
  await t.pumpAndSettle();
  await t.enterText(find.byKey(WeighInSheet.kgKey), kg);
  await t.pumpAndSettle();
}

PendingWeighIn _row(String id, {String date = '2026-11-07', num kg = 70}) =>
    PendingWeighIn(
      clientId: id,
      localDate: date,
      weightKg: kg.toDouble(),
      confirmUnusual: false,
      status: WeighInStatus.pending,
      attempts: 0,
    );

void main() {
  testWidgets('saves a weigh-in with the same-time tip', (t) async {
    final env = WeightsEnv();
    await pumpWeights(t, env);
    await _enter(t, '70.4');
    expect(find.text(en.weightTipSameTime), findsOneWidget);
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    final (_, body) = env.weights.puts.single;
    expect(body.weightKg, 70.4);
    expect(body.confirmUnusual, isFalse);
    expect(body.clientId, isNotNull);
    expect(find.byKey(WeighInSheet.kgKey), findsNothing);
  });

  testWidgets('needs confirm then save anyway', (t) async {
    final env = WeightsEnv();
    env.weights.putErrors.add(
      apiError(
        422,
        'weight_needs_confirm',
        details: {'previous': 70.5, 'previous_date': '2026-11-01'},
      ),
    );
    await pumpWeights(t, env);
    await _enter(t, '120');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.weightConfirmUnusual('70.5')), findsOneWidget);
    expect(env.weights.puts.single.$2.confirmUnusual, isFalse);

    await t.tap(find.byKey(WeighInSheet.saveAnywayKey));
    await t.pumpAndSettle();
    expect(env.weights.puts, hasLength(2));
    expect(env.weights.puts.last.$2.confirmUnusual, isTrue);
    expect(env.weights.puts.last.$2.weightKg, 120);
    expect(find.byKey(WeighInSheet.kgKey), findsNothing);
  });

  testWidgets('hidden previous shows hidden copy', (t) async {
    final env = WeightsEnv();
    env.weights.putErrors.add(
      apiError(422, 'weight_needs_confirm', details: {'previous': null}),
    );
    await pumpWeights(t, env);
    await _enter(t, '120');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.weightConfirmUnusualHidden), findsOneWidget);
    expect(find.textContaining('kg)'), findsNothing);
  });

  testWidgets('out of range shows its error and keeps the sheet', (t) async {
    final env = WeightsEnv();
    env.weights.putErrors.add(apiError(422, 'weight_out_of_range'));
    await pumpWeights(t, env);
    await _enter(t, '1');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.errorWeightOutOfRange), findsOneWidget);
  });

  testWidgets('offline weigh-in queues and shows waiting', (t) async {
    final env = WeightsEnv();
    env.weights.putErrors.add(networkError());
    await pumpWeights(t, env);
    await _enter(t, '70');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    final row = env.queue.weighIns.values.single;
    expect(row.weightKg, 70);
    expect(row.status, WeighInStatus.pending);
    expect(find.text(en.diaryWaitingSync), findsOneWidget);
    expect(find.byKey(WeightList.pendingKey(row.clientId)), findsOneWidget);
    expect(find.textContaining('70 kg'), findsOneWidget);
  });

  testWidgets('hide_all offline weigh-in shows no number', (t) async {
    final env = WeightsEnv(trend: 'hide_all');
    env.weights.putErrors.add(networkError());
    await pumpWeights(t, env);
    await _enter(t, '70');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    expect(find.text(en.diaryWaitingSync), findsOneWidget);
    expect(find.textContaining('70'), findsNothing);
    expect(find.textContaining('kg'), findsNothing);
  });

  testWidgets('sync needs confirm marks check entry', (t) async {
    final env = WeightsEnv();
    final h = await pumpWeights(t, env);
    await env.queue.addWeighIn(_row('w1'));
    env.weights.putErrors.add(
      apiError(422, 'weight_needs_confirm', details: {'previous': 70.5}),
    );
    await t.pumpAndSettle();
    expect(find.text(en.diaryWaitingSync), findsOneWidget);
    await t.runAsync(() => WeighInSync(env.weights, env.queue).flush());
    await t.pumpAndSettle();
    expect(env.queue.weighIns['w1']!.status, WeighInStatus.needsConfirm);
    expect(find.text(en.weightCheckEntry), findsOneWidget);

    // Confirming sends it again, with confirm_unusual, and it is stored.
    await t.tap(find.byKey(WeightList.confirmPendingKey('w1')));
    await t.pumpAndSettle();
    expect(env.weights.puts.last.$2.confirmUnusual, isTrue);
    expect(env.weights.puts.last.$2.clientId, 'w1');
    expect(env.queue.weighIns, isEmpty);
    expect(h.container, isNotNull);
  });

  testWidgets('edit sends the same day, delete asks first', (t) async {
    final env = WeightsEnv();
    await pumpWeights(t, env);
    await t.tap(find.byKey(WeightList.editKey('2026-01-10')));
    await t.pumpAndSettle();
    expect(find.text(en.weightEdit), findsOneWidget);
    await t.enterText(find.byKey(WeighInSheet.kgKey), '78.5');
    await t.tap(find.byKey(WeighInSheet.saveKey));
    await t.pumpAndSettle();
    expect(env.weights.puts.single.$1, DateTime.utc(2026, 1, 10));
    expect(env.weights.puts.single.$2.weightKg, 78.5);

    await t.tap(find.byKey(WeightList.deleteKey('2026-01-10')));
    await t.pumpAndSettle();
    expect(find.text(en.weightDeleteConfirm), findsOneWidget);
    await t.tap(find.byKey(const Key('weight-delete-confirm')));
    await t.pumpAndSettle();
    expect(env.weights.deletes.single, DateTime.utc(2026, 1, 10));
  });

  test('delete works without consent gating on the client', () async {
    final client = FakeWeightsClient();
    final repo = WeightsRepository(client, MemoryMealQueue());
    await repo.delete('2026-01-10');
    expect(client.deletes.single, DateTime.utc(2026, 1, 10));
    client.deleteError = apiError(404, 'weight_not_found');
    await expectLater(
      repo.delete('2026-01-11'),
      throwsA(
        isA<WeightsFailure>().having((e) => e.code, 'code', 'weight_not_found'),
      ),
    );
  });
}
