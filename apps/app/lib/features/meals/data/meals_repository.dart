// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../domain/meal_draft.dart';
import 'meal_sync.dart';

/// A failed meals call. [code] is the API `error.code` (`portion_required`,
/// `meal_not_found`, ...), `network` when there was no response, or null;
/// screens map it with `localizedErrorCode`.
class MealsFailure implements Exception {
  const MealsFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw MealsFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'MealsFailure($code)';
}

/// What [MealsRepository.log] did.
sealed class MealLogResult {
  const MealLogResult();
}

/// The API stored it (201, or 200 for a known `client_id`).
class MealLogged extends MealLogResult {
  const MealLogged(this.meal);
  final MealOut meal;
}

/// Kept on the phone (offline, 5xx or 429); [MealSync.flush] sends it later
/// with the same [clientId].
class MealQueued extends MealLogResult {
  const MealQueued(this.clientId);
  final String clientId;
}

/// Wraps the generated `MealsClient` and the offline queue.
class MealsRepository {
  MealsRepository(this._client, this._queue, this._sync, {Uuid? uuid})
    : _uuid = uuid ?? const Uuid();

  final MealsClient _client;
  final MealQueue _queue;
  final MealSync _sync;
  final Uuid _uuid;

  /// Writes [draft] to the queue with a new `client_id` (uuid v4), then
  /// posts it. Returns [MealLogged] on 201/200 and [MealQueued] when it
  /// could not be sent yet. A refusal (4xx other than 429) removes the row
  /// and throws [MealsFailure], so the user can fix the portion right away.
  Future<MealLogResult> log(MealDraft draft) async {
    final row = PendingMeal(
      clientId: _uuid.v4(),
      memberId: draft.memberId,
      productId: draft.productId,
      barcode: draft.barcode,
      grams: draft.grams?.toDouble(),
      servings: draft.servings?.toDouble(),
      eatenAt: draft.eatenAt.toUtc(),
      attempts: 0,
    );
    await _queue.add(row);
    try {
      return MealLogged(await _sync.send(row));
    } on Object catch (e) {
      if (isRetryable(e)) return MealQueued(row.clientId);
      await _queue.remove(row.clientId);
      throw MealsFailure(apiErrorCode(e), e);
    }
  }

  /// A member's logs, newest first (the API's default range: the last 7 IST
  /// days).
  Future<List<MealOut>> list(String memberId) =>
      MealsFailure.guard(() => _client.mealsList(memberId: memberId));

  /// Undo or remove a stored log.
  Future<void> delete(String mealId) =>
      MealsFailure.guard(() => _client.mealsDelete(mealId: mealId));
}
