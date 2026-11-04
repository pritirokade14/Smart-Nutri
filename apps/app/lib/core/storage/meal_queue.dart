import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'meal_queue.g.dart';

/// "I ate this" logs waiting to reach the API (F8, Android offline log).
///
/// Every log is written here first with a fresh `clientId` (uuid v4) and is
/// deleted only once `POST /v1/meals` answered 201/200. Retries always send
/// the stored `clientId`, so the API never stores a log twice.
///
/// A row whose `lastError` is set was refused by the API (a 4xx other than
/// 429): it is never sent again and only kept so the app can say so.
class PendingMeals extends Table {
  TextColumn get clientId => text()();
  TextColumn get memberId => text()();

  /// Exactly one of [productId] (our product) and [barcode] (an Open Food
  /// Facts product) is set.
  TextColumn get productId => text().nullable()();
  TextColumn get barcode => text().nullable()();

  /// Exactly one of [grams] and [servings] is set.
  RealColumn get grams => real().nullable()();
  RealColumn get servings => real().nullable()();

  /// When it was eaten (stored as UTC), sent as `eaten_at`.
  DateTimeColumn get eatenAt => dateTime()();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();

  @override
  Set<Column<Object>> get primaryKey => {clientId};
}

@DriftDatabase(tables: [PendingMeals])
class MealQueueDatabase extends _$MealQueueDatabase {
  MealQueueDatabase(super.e);

  /// The on-device database file.
  factory MealQueueDatabase.open() =>
      MealQueueDatabase(driftDatabase(name: 'smartnutri_meal_queue'));

  @override
  int get schemaVersion => 1;
}

/// The offline log queue. [DriftMealQueue] is the app's; tests may use an
/// in-memory one.
abstract interface class MealQueue {
  Future<void> add(PendingMeal meal);

  /// Rows still to send (no `lastError`), oldest `eatenAt` first.
  Future<List<PendingMeal>> pending();

  Future<void> remove(String clientId);

  /// A 5xx, 429 or network failure: keep the row, `attempts + 1`.
  Future<void> recordAttempt(String clientId, String error);

  /// A 4xx refusal: the row is never sent again.
  Future<void> markFailed(String clientId, String error);

  /// Number of rows still to send.
  Stream<int> watchPendingCount();

  /// Number of rows the API refused.
  Stream<int> watchFailedCount();

  /// Forgets the refused rows (after the user saw the notice).
  Future<void> clearFailed();

  /// Forgets every row, sent or not. Called before the session ends, so the
  /// next person on this phone never inherits (or sends) this one's logs.
  Future<void> clearAll();
}

class DriftMealQueue implements MealQueue {
  DriftMealQueue(this._db);

  final MealQueueDatabase _db;

  $PendingMealsTable get _t => _db.pendingMeals;

  @override
  Future<void> add(PendingMeal meal) => _db.into(_t).insert(meal);

  @override
  Future<List<PendingMeal>> pending() =>
      (_db.select(_t)
            ..where((r) => r.lastError.isNull())
            ..orderBy([
              (r) => OrderingTerm.asc(r.eatenAt),
              (r) => OrderingTerm.asc(r.clientId),
            ]))
          .get();

  @override
  Future<void> remove(String clientId) =>
      (_db.delete(_t)..where((r) => r.clientId.equals(clientId))).go();

  @override
  Future<void> recordAttempt(String clientId, String error) => _db.customUpdate(
    'UPDATE pending_meals SET attempts = attempts + 1 '
    'WHERE client_id = ?',
    variables: [Variable.withString(clientId)],
    updates: {_t},
  );

  @override
  Future<void> markFailed(String clientId, String error) =>
      (_db.update(_t)..where((r) => r.clientId.equals(clientId))).write(
        PendingMealsCompanion(lastError: Value(error)),
      );

  Stream<int> _count(Expression<bool> Function($PendingMealsTable) where) {
    final count = _t.clientId.count();
    return (_db.selectOnly(_t)
          ..addColumns([count])
          ..where(where(_t)))
        .map((row) => row.read(count) ?? 0)
        .watchSingle();
  }

  @override
  Stream<int> watchPendingCount() => _count((r) => r.lastError.isNull());

  @override
  Stream<int> watchFailedCount() => _count((r) => r.lastError.isNotNull());

  @override
  Future<void> clearFailed() =>
      (_db.delete(_t)..where((r) => r.lastError.isNotNull())).go();

  @override
  Future<void> clearAll() => _db.delete(_t).go();
}
