import 'dart:async';

import 'package:dio/dio.dart';
import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:smartnutri_ai/core/storage/meal_queue.dart';
import 'package:smartnutri_ai/features/meals/presentation/meals_providers.dart';
import 'package:smartnutri_api/src/export.dart';

/// A request that never got a response (offline, DNS, timeout).
DioException networkError() => DioException(
  requestOptions: RequestOptions(path: '/v1/meals'),
  type: DioExceptionType.connectionError,
);

/// An API error with the standard envelope.
DioException apiError(
  int status,
  String code, {
  Map<String, Object?> details = const {},
}) {
  final options = RequestOptions(path: '/v1/meals');
  return DioException(
    requestOptions: options,
    type: DioExceptionType.badResponse,
    response: Response<Object?>(
      requestOptions: options,
      statusCode: status,
      data: {
        'error': {
          'code': code,
          'message_key': 'error.$code',
          'details': <String, Object?>{...details},
        },
      },
    ),
  );
}

MealOut mealOut({
  String id = 'meal-1',
  String memberId = 'm1',
  String productName = 'Sugar Free Biscuit',
  String? clientId,
  num grams = 30,
  DateTime? eatenAt,
  String? barcode,
  String? attribution,
  NutriScoreGrade? grade = NutriScoreGrade.d,
}) => MealOut(
  incomplete: const [],
  localDate: DateTime.utc(2026, 11, 3),
  mealSlotId: 'slot-1',
  sourceKind: barcode == null
      ? MealOutSourceKind.product
      : MealOutSourceKind.off,
  updatedAt: eatenAt ?? DateTime.utc(2026, 11, 3, 8),
  attribution: attribution,
  barcode: barcode,
  clientId: clientId,
  eatenAt: eatenAt ?? DateTime.utc(2026, 11, 3, 8),
  grade: grade,
  grams: grams,
  id: id,
  memberId: memberId,
  nutrients: const NutrientSnapshot(
    carbsG: null,
    energyKcal: 140,
    fatG: null,
    fibreG: null,
    proteinG: 2,
    saltG: 0.3,
    satFatG: null,
    sugarsG: null,
  ),
  productId: barcode == null ? 'p1' : null,
  productName: productName,
);

/// Records every call. `logResponses` answers `mealsLog` in order (a
/// [MealOut] or an error to throw); when it runs out, the call succeeds.
class FakeMealsClient implements MealsClient {
  FakeMealsClient({List<Object>? logResponses})
    : logResponses = logResponses ?? [];

  final List<Object> logResponses;
  final logged = <MealIn>[];
  final deleted = <String>[];
  final summaries = <(String, SummaryPeriod?, DateTime?)>[];

  /// `mealsLog` waits for this when set (to test in-flight state).
  Completer<void>? gate;

  List<MealOut> meals = [];
  Object? listError;
  Summary? Function(String memberId, SummaryPeriod? period)? summary;
  Object? summaryError;
  WeekCounts weekCounts = WeekCounts(
    start: DateTime.utc(2026, 10, 28),
    end: DateTime.utc(2026, 11, 3),
    scans: 12,
    logged: 10,
  );

  @override
  Future<MealOut> mealsLog({required MealIn body}) async {
    logged.add(body);
    await gate?.future;
    if (logResponses.isNotEmpty) {
      final r = logResponses.removeAt(0);
      if (r is MealOut) return r;
      throw r;
    }
    return mealOut(
      id: 'meal-${logged.length}',
      memberId: body.memberId ?? 'm1',
      clientId: body.clientId,
    );
  }

  final copied = <CopyIn>[];
  final updated = <(String, MealPatch)>[];

  /// What `mealsCopy` answers in order (a [CopyOut] or an error to throw);
  /// when it runs out, one copy per call succeeds.
  final copyResponses = <Object>[];

  /// Thrown by the next `mealsUpdate` (then cleared).
  Object? updateError;

  @override
  Future<CopyOut> mealsCopy({required CopyIn body}) async {
    copied.add(body);
    if (copyResponses.isNotEmpty) {
      final r = copyResponses.removeAt(0);
      if (r is CopyOut) return r;
      throw r;
    }
    return CopyOut(created: [mealOut(id: 'copy-${copied.length}')]);
  }

  @override
  Future<MealOut> mealsUpdate({
    required String mealId,
    required MealPatch body,
  }) async {
    updated.add((mealId, body));
    if (updateError case final e?) {
      updateError = null;
      throw e;
    }
    return mealOut(id: mealId);
  }

  @override
  Future<List<MealOut>> mealsList({
    String? memberId,
    DateTime? from,
    DateTime? localDate,
    DateTime? to,
  }) async {
    final e = listError;
    if (e != null) throw e;
    return [
      for (final m in meals)
        if (m.memberId == memberId) m,
    ];
  }

  @override
  Future<Summary> mealsSummary({
    required String memberId,
    DateTime? date,
    SummaryPeriod? period = SummaryPeriod.day,
  }) async {
    summaries.add((memberId, period, date));
    final e = summaryError;
    if (e != null) throw e;
    final s = summary?.call(memberId, period);
    if (s == null) throw apiError(404, 'member_not_found');
    return s;
  }

  @override
  Future<WeekCounts> mealsWeekCounts({DateTime? date}) async => weekCounts;

  /// Thrown by the next `mealsDelete` (then cleared).
  Object? deleteError;

  @override
  Future<void> mealsDelete({required String mealId}) async {
    if (deleteError case final e?) {
      deleteError = null;
      throw e;
    }
    deleted.add(mealId);
    meals = [
      for (final m in meals)
        if (m.id != mealId) m,
    ];
  }
}

/// An in-memory [MealQueue] for widget tests (no sqlite, no timers).
class MemoryMealQueue implements MealQueue {
  final rows = <String, PendingMeal>{};
  final _changes = StreamController<void>.broadcast();

  void _changed() => _changes.add(null);

  @override
  Future<void> add(PendingMeal meal) async {
    rows[meal.clientId] = meal;
    _changed();
  }

  @override
  Future<List<PendingMeal>> pending() async =>
      rows.values.where((r) => r.lastError == null).toList()
        ..sort((a, b) => a.eatenAt.compareTo(b.eatenAt));

  @override
  Future<void> remove(String clientId) async {
    rows.remove(clientId);
    _changed();
  }

  @override
  Future<void> recordAttempt(String clientId, String error) async {
    final r = rows[clientId];
    if (r != null) rows[clientId] = r.copyWith(attempts: r.attempts + 1);
    _changed();
  }

  @override
  Future<void> markFailed(String clientId, String error) async {
    final r = rows[clientId];
    if (r != null) rows[clientId] = r.copyWith(lastError: Value(error));
    _changed();
  }

  Stream<int> _watch(bool Function(PendingMeal) test) async* {
    yield rows.values.where(test).length;
    await for (final _ in _changes.stream) {
      yield rows.values.where(test).length;
    }
  }

  @override
  Stream<List<PendingMeal>> watchPending() async* {
    yield await pending();
    await for (final _ in _changes.stream) {
      yield await pending();
    }
  }

  @override
  Stream<int> watchPendingCount() => _watch((r) => r.lastError == null);

  @override
  Stream<int> watchFailedCount() => _watch(
    (r) => r.lastError != null && !needsSlotErrors.contains(r.lastError),
  );

  @override
  Stream<List<PendingMeal>> watchNeedingSlot() async* {
    List<PendingMeal> now() =>
        rows.values.where((r) => needsSlotErrors.contains(r.lastError)).toList();
    yield now();
    await for (final _ in _changes.stream) {
      yield now();
    }
  }

  @override
  Future<void> retryWithSlot(String clientId, String slotId) async {
    final r = rows[clientId];
    if (r != null) {
      rows[clientId] = r.copyWith(
        mealSlotId: Value(slotId),
        lastError: const Value(null),
      );
    }
    _changed();
  }

  @override
  Future<void> clearFailed() async {
    rows.removeWhere(
      (_, r) => r.lastError != null && !needsSlotErrors.contains(r.lastError),
    );
    _changed();
  }

  /// Called by [clearAll], for tests that check the order of calls.
  void Function()? onClearAll;

  @override
  Future<void> clearAll() async {
    onClearAll?.call();
    rows.clear();
    _changed();
  }
}

/// Overrides that keep the offline log and its sync triggers off the
/// platform (no sqlite, no connectivity plugin) in widget tests.
List<Override> mealTestOverrides({MealQueue? queue, MealsClient? client}) => [
  mealQueueProvider.overrideWithValue(queue ?? MemoryMealQueue()),
  connectivityRegainedProvider.overrideWithValue(const Stream<void>.empty()),
  if (client != null) mealsClientProvider.overrideWithValue(client),
];
