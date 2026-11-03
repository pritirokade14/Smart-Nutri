import 'dart:async';

import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/meals/data/meal_sync.dart';
import 'package:smartnutri_ai/features/meals/data/meals_repository.dart';
import 'package:smartnutri_ai/features/meals/domain/meal_draft.dart';

import '../../support/fake_meals.dart';

MealDraft _draft({
  String memberId = 'm1',
  String? productId = 'p1',
  String? barcode,
  num? grams = 30,
  num? servings,
  DateTime? eatenAt,
}) => MealDraft(
  memberId: memberId,
  productId: productId,
  barcode: barcode,
  grams: grams,
  servings: servings,
  eatenAt: eatenAt ?? DateTime.utc(2026, 11, 3, 8),
);

void main() {
  late MealQueueDatabase db;
  late DriftMealQueue queue;

  setUp(() {
    db = MealQueueDatabase(NativeDatabase.memory());
    queue = DriftMealQueue(db);
  });
  tearDown(() => db.close());

  ({FakeMealsClient api, MealSync sync, MealsRepository repo}) build(
    List<Object> responses,
  ) {
    final api = FakeMealsClient(logResponses: responses);
    final sync = MealSync(api, queue);
    return (api: api, sync: sync, repo: MealsRepository(api, queue, sync));
  }

  test('sync retries do not duplicate', () async {
    final h = build([networkError()]);

    // Offline: the log is kept on the phone.
    final first = await h.repo.log(_draft());
    expect(first, isA<MealQueued>());
    final queued = await queue.pending();
    expect(queued, hasLength(1));
    expect(queued.single.attempts, 1);

    // Back online: the same client_id goes again and the API says 200.
    final result = await h.sync.flush();
    expect(result.sent, 1);
    expect(await queue.pending(), isEmpty);

    expect(h.api.logged, hasLength(2));
    final ids = h.api.logged.map((b) => b.clientId).toSet();
    expect(ids, hasLength(1), reason: 'both attempts carry the same clientId');
    expect(ids.single, queued.single.clientId);
    expect(
      RegExp(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
      ).hasMatch(ids.single!),
      isTrue,
      reason: 'uuid v4',
    );

    // A further flush sends nothing.
    final again = await h.sync.flush();
    expect(again.sent, 0);
    expect(h.api.logged, hasLength(2));
  });

  test('4xx drops row', () async {
    final h = build([networkError(), apiError(422, 'eaten_at_out_of_range')]);
    await h.repo.log(_draft());
    expect(await queue.pending(), hasLength(1));

    final result = await h.sync.flush();
    expect(result.failed, 1);
    expect(await queue.pending(), isEmpty, reason: 'never sent again');
    expect(await queue.watchFailedCount().first, 1);
    final row = await db.select(db.pendingMeals).getSingle();
    expect(row.lastError, 'eaten_at_out_of_range');

    await h.sync.flush();
    expect(h.api.logged, hasLength(2), reason: 'a refused row is not retried');

    await queue.clearFailed();
    expect(await queue.watchFailedCount().first, 0);
  });

  test('5xx and 429 keep the row with attempts + 1', () async {
    final h = build([
      networkError(),
      apiError(503, 'internal_error'),
      apiError(429, 'rate_limited'),
    ]);
    await h.repo.log(_draft());
    await h.sync.flush();
    await h.sync.flush();
    final rows = await queue.pending();
    expect(rows, hasLength(1));
    expect(rows.single.attempts, 3);
    expect(rows.single.lastError, isNull);
  });

  test(
    'flush posts queued rows in eatenAt order with their clientIds',
    () async {
      final h = build([networkError(), networkError(), networkError()]);
      await h.repo.log(_draft(eatenAt: DateTime.utc(2026, 11, 3, 12)));
      await h.repo.log(_draft(eatenAt: DateTime.utc(2026, 11, 2, 9)));
      await h.repo.log(
        _draft(
          productId: null,
          barcode: '8901063201089',
          grams: null,
          servings: 2,
          eatenAt: DateTime.utc(2026, 11, 3, 7),
        ),
      );
      final stored = await queue.pending();
      h.api.logged.clear();

      final result = await h.sync.flush();
      expect(result.sent, 3);
      expect(h.api.logged.map((b) => b.eatenAt), [
        DateTime.utc(2026, 11, 2, 9),
        DateTime.utc(2026, 11, 3, 7),
        DateTime.utc(2026, 11, 3, 12),
      ]);
      expect(
        h.api.logged.map((b) => b.clientId).toList(),
        stored.map((r) => r.clientId).toList(),
      );
      final off = h.api.logged[1];
      expect(off.barcode, '8901063201089');
      expect(off.productId, isNull);
      expect(off.servings, 2);
      expect(off.grams, isNull);
      // Always timezone-aware on the wire.
      expect(off.toJson()['eaten_at'], '2026-11-03T07:00:00.000Z');
    },
  );

  test('a network failure stops the flush; the rest stay queued', () async {
    final h = build([networkError(), networkError(), networkError()]);
    await h.repo.log(_draft(eatenAt: DateTime.utc(2026, 11, 2)));
    await h.repo.log(_draft(eatenAt: DateTime.utc(2026, 11, 3)));
    h.api.logged.clear();
    h.api.logResponses.add(networkError());

    final result = await h.sync.flush();
    expect(result.sent, 0);
    expect(h.api.logged, hasLength(1), reason: 'offline: stop after the first');
    expect(await queue.pending(), hasLength(2));
  });

  test('concurrent flushes share one run', () async {
    final h = build([networkError()]);
    await h.repo.log(_draft());
    h.api.logged.clear();
    final a = h.sync.flush();
    final b = h.sync.flush();
    await Future.wait([a, b]);
    expect(h.api.logged, hasLength(1));
  });

  group('MealsRepository.log', () {
    test('online: posts with a new clientId and empties the queue', () async {
      final h = build([]);
      final result = await h.repo.log(_draft());
      expect(result, isA<MealLogged>());
      expect((result as MealLogged).meal.id, 'meal-1');
      expect(await queue.pending(), isEmpty);
      final body = h.api.logged.single;
      expect(body.memberId, 'm1');
      expect(body.productId, 'p1');
      expect(body.grams, 30);
      expect(body.servings, isNull);
      expect(body.clientId, isNotNull);
    });

    test('each log gets a fresh clientId', () async {
      final h = build([]);
      await h.repo.log(_draft());
      await h.repo.log(_draft());
      expect(h.api.logged[0].clientId, isNot(h.api.logged[1].clientId));
    });

    test('a 4xx at log time is reported and nothing stays queued', () async {
      final h = build([apiError(422, 'serving_size_unknown')]);
      await expectLater(
        h.repo.log(_draft(grams: null, servings: 1)),
        throwsA(
          isA<MealsFailure>().having(
            (f) => f.code,
            'code',
            'serving_size_unknown',
          ),
        ),
      );
      expect(await queue.pending(), isEmpty);
      expect(await queue.watchFailedCount().first, 0);
    });

    test('a 5xx at log time keeps the row for sync', () async {
      final h = build([apiError(500, 'internal_error')]);
      expect(await h.repo.log(_draft()), isA<MealQueued>());
      expect(await queue.pending(), hasLength(1));
    });

    test('flush skips a row whose log call is still in flight', () async {
      final h = build([]);
      final gate = h.api.gate = Completer<void>();
      final logging = h.repo.log(_draft());
      await Future<void>.delayed(Duration.zero);
      await h.sync.flush();
      gate.complete();
      await logging;
      expect(h.api.logged, hasLength(1));
    });
  });
}
