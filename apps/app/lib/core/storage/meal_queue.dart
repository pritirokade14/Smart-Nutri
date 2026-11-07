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
  int get schemaVersion => 3;

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
  Future<void> clearAll() => _db.delete(_t).go();
}
