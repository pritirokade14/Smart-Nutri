import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'meal_queue.g.dart';

/// "I ate this" logs waiting to reach the API (F8, Android offline log).
///
/// Every log is written here first with a fresh `clientId` (uuid v4) and is
/// deleted only once `POST /v1/meals` answered 201/200. Retries always send
/// the stored `clientId`, so the API never stores a log twice.
///
/// `lastError` of a row whose meal slot was archived before it synced.
const mealSlotArchivedError = 'meal_slot_archived';

/// `lastError` of a row whose meal slot was deleted before it synced (404).
const mealSlotNotFoundError = 'meal_slot_not_found';

/// The errors after which a row waits for the user to pick another meal.
const needsSlotErrors = [mealSlotArchivedError, mealSlotNotFoundError];

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

  /// When it was eaten (stored as UTC), sent as `eaten_at` (unless
  /// [localDate] is set).
  DateTimeColumn get eatenAt => dateTime()();

  // Queue schema v2 (Plan 11, Ruling E19). Rows queued by the v1 app have
  // none of these: they sync with no slot (the API picks one) and their
  // `eatenAt`.

  /// The meal slot chosen, or null (the API picks from the clock).
  TextColumn get mealSlotId => text().nullable()();

  /// A past day (`2026-11-06`) the entry belongs to; sent as `local_date`
  /// instead of `eaten_at`.
  TextColumn get localDate => text().nullable()();

  /// A quick add: set when [quickEnergyKcal] is. Blank fields stay null,
  /// never 0.
  TextColumn get quickName => text().nullable()();
  RealColumn get quickEnergyKcal => real().nullable()();
  RealColumn get quickProteinG => real().nullable()();
  RealColumn get quickFatG => real().nullable()();
  RealColumn get quickCarbsG => real().nullable()();
  RealColumn get quickFibreG => real().nullable()();

  /// The name shown on the pending row (a product name or a quick-add name).
  /// User text: never sent to analytics.
  TextColumn get displayName => text().nullable()();

  // Queue schema v3 (Plan 12 slice 3). A generic food or dish and a
  // household-unit portion; rows queued by older apps have none of these.

  /// A generic food or Indian dish (`foods.id`).
  TextColumn get foodId => text().nullable()();

  /// A household-unit portion: [quantity] of [unit] (a unit code), instead
  /// of [grams] and [servings]. The API converts it.
  RealColumn get quantity => real().nullable()();
  TextColumn get unit => text().nullable()();
  // Queue schema v4 (Plan 12 slice 4). One of your own custom foods or
  // recipes; rows queued by older apps have none of these.

  /// One of the account's custom foods (`custom_foods.id`).
  TextColumn get customFoodId => text().nullable()();

  /// One of the account's recipes (`recipes.id`).
  TextColumn get recipeId => text().nullable()();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();

  @override
  Set<Column<Object>> get primaryKey => {clientId};
}

/// `PendingWeighIns.status`: waiting to be sent.
class WeighInStatus {
  static const pending = 'pending';

  /// The API asked for a confirmation (`weight_needs_confirm`): the row waits
  /// for the user.
  static const needsConfirm = 'needs_confirm';

  /// Any other refusal: never sent again.
  static const failed = 'failed';
}

/// Weigh-ins made offline (queue schema v5, Plan 12 slice 6). One row per
/// day: a later one replaces it, like the API's `PUT /v1/weights/{day}`.
class PendingWeighIns extends Table {
  TextColumn get clientId => text()();

  /// The day (`2026-11-07`) as shown by the diary.
  TextColumn get localDate => text()();
  RealColumn get weightKg => real()();
  BoolColumn get confirmUnusual =>
      boolean().withDefault(const Constant(false))();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  IntColumn get attempts => integer().withDefault(const Constant(0))();

  /// The API error code of a refusal (status `failed`).
  TextColumn get lastError => text().nullable()();

  @override
  Set<Column<Object>> get primaryKey => {clientId};
}

@DriftDatabase(tables: [PendingMeals, PendingWeighIns])
class MealQueueDatabase extends _$MealQueueDatabase {
  MealQueueDatabase(super.e);

  /// The on-device database file.
  factory MealQueueDatabase.open() =>
      MealQueueDatabase(driftDatabase(name: 'smartnutri_meal_queue'));

  @override
  int get schemaVersion => 6;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (m) => m.createAll(),
    onUpgrade: (m, from, to) async {
      if (from < 2) {
        await m.addColumn(pendingMeals, pendingMeals.mealSlotId);
        await m.addColumn(pendingMeals, pendingMeals.localDate);
        await m.addColumn(pendingMeals, pendingMeals.quickName);
        await m.addColumn(pendingMeals, pendingMeals.quickEnergyKcal);
        await m.addColumn(pendingMeals, pendingMeals.quickProteinG);
        await m.addColumn(pendingMeals, pendingMeals.quickFatG);
        await m.addColumn(pendingMeals, pendingMeals.quickCarbsG);
        await m.addColumn(pendingMeals, pendingMeals.quickFibreG);
        await m.addColumn(pendingMeals, pendingMeals.displayName);
      }
      if (from < 3) {
        await m.addColumn(pendingMeals, pendingMeals.foodId);
        await m.addColumn(pendingMeals, pendingMeals.quantity);
        await m.addColumn(pendingMeals, pendingMeals.unit);
      }
      if (from < 4) {
        await m.addColumn(pendingMeals, pendingMeals.customFoodId);
        await m.addColumn(pendingMeals, pendingMeals.recipeId);
      }
      if (from < 5) {
        await m.createTable(pendingWeighIns);
      }
      if (from == 5) {
        await m.addColumn(pendingWeighIns, pendingWeighIns.lastError);
      }
    },
  );
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

  /// The rows still to send, as they change (for the pending rows of the
  /// Diary).
  Stream<List<PendingMeal>> watchPending();

  /// Number of rows still to send.
  Stream<int> watchPendingCount();

  /// Number of rows the API refused (not those waiting for a new meal).
  Stream<int> watchFailedCount();

  /// Rows refused because their meal was removed: they wait for the user to
  /// pick another meal ([retryWithSlot]).
  Stream<List<PendingMeal>> watchNeedingSlot();

  /// Gives a refused row a new meal and makes it sendable again. The
  /// `clientId` stays, so a retry never stores the entry twice.
  Future<void> retryWithSlot(String clientId, String slotId);

  /// Forgets the refused rows (after the user saw the notice).
  Future<void> clearFailed();

  /// Forgets every row, sent or not. Called before the session ends, so the
  /// next person on this phone never inherits (or sends) this one's logs.
  Future<void> clearAll();
}

/// The offline weigh-in queue (Plan 12 slice 6).
abstract interface class WeighInQueue {
  /// Stores [row]; any row for the same day is replaced.
  Future<void> addWeighIn(PendingWeighIn row);

  /// Rows still to send (status `pending`), oldest day first.
  Future<List<PendingWeighIn>> pendingWeighIns();

  /// Rows to show: `pending` and `needs_confirm`, as they change.
  Stream<List<PendingWeighIn>> watchWeighIns();

  Future<void> removeWeighIn(String clientId);

  /// A 5xx, 429 or network failure: keep the row, `attempts + 1`.
  Future<void> recordWeighInAttempt(String clientId);

  Future<void> setWeighInStatus(
    String clientId,
    String status, {
    String? error,
  });

  /// The error codes of the refused weigh-ins (one entry per row; `null`
  /// when no code was stored).
  Stream<List<String?>> watchFailedWeighIns();

  /// Forgets the refused weigh-ins, kilograms included (after the user saw
  /// the notice).
  Future<void> clearFailedWeighIns();

  /// The user confirmed an unusual value: send it again with
  /// `confirm_unusual`.
  Future<void> confirmWeighIn(String clientId);

  /// Forgets every queued weigh-in (the user erased their weight history,
  /// so nothing may upload later).
  Future<void> clearWeighIns();
}

class DriftMealQueue implements MealQueue, WeighInQueue {
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
  Stream<List<PendingMeal>> watchPending() =>
      (_db.select(_t)
            ..where((r) => r.lastError.isNull())
            ..orderBy([(r) => OrderingTerm.asc(r.eatenAt)]))
          .watch();

  @override
  Stream<int> watchPendingCount() => _count((r) => r.lastError.isNull());

  @override
  Stream<int> watchFailedCount() => _count(
    (r) => r.lastError.isNotNull() & r.lastError.isIn(needsSlotErrors).not(),
  );

  @override
  Stream<List<PendingMeal>> watchNeedingSlot() =>
      (_db.select(_t)
            ..where((r) => r.lastError.isIn(needsSlotErrors))
            ..orderBy([(r) => OrderingTerm.asc(r.eatenAt)]))
          .watch();

  @override
  Future<void> retryWithSlot(String clientId, String slotId) =>
      (_db.update(_t)..where((r) => r.clientId.equals(clientId))).write(
        PendingMealsCompanion(
          mealSlotId: Value(slotId),
          lastError: const Value(null),
        ),
      );

  @override
  Future<void> clearFailed() =>
      (_db.delete(_t)..where(
            (r) =>
                r.lastError.isNotNull() &
                r.lastError.isIn(needsSlotErrors).not(),
          ))
          .go();

  @override
  Future<void> clearAll() async {
    await _db.delete(_t).go();
    await _db.delete(_w).go();
  }

  $PendingWeighInsTable get _w => _db.pendingWeighIns;

  @override
  Future<void> clearWeighIns() => _db.delete(_w).go();

  @override
  Future<void> addWeighIn(PendingWeighIn row) => _db.transaction(() async {
    await (_db.delete(
      _w,
    )..where((r) => r.localDate.equals(row.localDate))).go();
    await _db.into(_w).insert(row);
  });

  @override
  Future<List<PendingWeighIn>> pendingWeighIns() =>
      (_db.select(_w)
            ..where((r) => r.status.equals(WeighInStatus.pending))
            ..orderBy([(r) => OrderingTerm.asc(r.localDate)]))
          .get();

  @override
  Stream<List<PendingWeighIn>> watchWeighIns() =>
      (_db.select(_w)
            ..where(
              (r) => r.status.isIn(const [
                WeighInStatus.pending,
                WeighInStatus.needsConfirm,
              ]),
            )
            ..orderBy([(r) => OrderingTerm.asc(r.localDate)]))
          .watch();

  @override
  Future<void> removeWeighIn(String clientId) =>
      (_db.delete(_w)..where((r) => r.clientId.equals(clientId))).go();

  @override
  Future<void> recordWeighInAttempt(String clientId) => _db.customUpdate(
    'UPDATE pending_weigh_ins SET attempts = attempts + 1 '
    'WHERE client_id = ?',
    variables: [Variable.withString(clientId)],
    updates: {_w},
  );

  @override
  Future<void> setWeighInStatus(
    String clientId,
    String status, {
    String? error,
  }) => (_db.update(_w)..where((r) => r.clientId.equals(clientId))).write(
    PendingWeighInsCompanion(status: Value(status), lastError: Value(error)),
  );

  @override
  Stream<List<String?>> watchFailedWeighIns() =>
      (_db.select(_w)..where((r) => r.status.equals(WeighInStatus.failed)))
          .watch()
          .map((rows) => [for (final r in rows) r.lastError]);

  @override
  Future<void> clearFailedWeighIns() => (_db.delete(
    _w,
  )..where((r) => r.status.equals(WeighInStatus.failed))).go();

  @override
  Future<void> confirmWeighIn(String clientId) =>
      (_db.update(_w)..where((r) => r.clientId.equals(clientId))).write(
        const PendingWeighInsCompanion(
          confirmUnusual: Value(true),
          status: Value(WeighInStatus.pending),
        ),
      );
}
