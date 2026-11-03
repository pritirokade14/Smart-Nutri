import 'package:dio/dio.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';

/// What one `POST /v1/meals` attempt came to.
enum SendOutcome {
  /// 201 or 200 (the `client_id` was already stored): the row is gone.
  sent,

  /// No response, a 5xx or a 429: kept, `attempts + 1`.
  retry,

  /// Any other 4xx: the API will never accept it.
  refused,
}

/// No response at all (offline, DNS, timeout).
bool isNetworkError(Object error) =>
    error is DioException && error.response == null;

/// Worth sending again with the same `client_id`: no response, a 5xx, a 429,
/// or a 2xx whose body could not be read (the API stored it; a retry with
/// the same id returns the stored row).
bool isRetryable(Object error) {
  if (error is! DioException) return true;
  final status = error.response?.statusCode;
  if (status == null) return true;
  return status >= 500 || status == 429 || status < 400;
}

/// The result of one [MealSync.flush].
typedef SyncResult = ({int sent, int failed, int kept});

/// Sends the offline log queue to the API. Rows go in `eatenAt` order with
/// their stored `client_id`, so a retry after a timeout never creates a
/// second log.
class MealSync {
  MealSync(this._client, this._queue);

  final MealsClient _client;
  final MealQueue _queue;

  /// Client ids being posted right now (by [send] or a flush).
  final _inFlight = <String>{};
  Future<SyncResult>? _running;

  /// Posts one queued row. On 201/200 the row is deleted and the stored log
  /// returned; a 4xx other than 429 marks it refused; anything else keeps it
  /// for the next flush. The error is rethrown in both failure cases.
  Future<MealOut> send(PendingMeal row) async {
    _inFlight.add(row.clientId);
    try {
      final meal = await _client.mealsLog(body: toMealIn(row));
      await _queue.remove(row.clientId);
      return meal;
    } on Object catch (e) {
      final code = apiErrorCode(e) ?? 'internal_error';
      if (isRetryable(e)) {
        await _queue.recordAttempt(row.clientId, code);
      } else {
        await _queue.markFailed(row.clientId, code);
      }
      rethrow;
    } finally {
      _inFlight.remove(row.clientId);
    }
  }

  /// Sends every queued row once. Runs on app start, on resume and when the
  /// connection comes back; concurrent calls share one run. Stops at the
  /// first network failure (still offline).
  Future<SyncResult> flush() => _running ??= _flush().whenComplete(() {
    _running = null;
  });

  Future<SyncResult> _flush() async {
    var sent = 0;
    var failed = 0;
    final rows = await _queue.pending();
    for (final row in rows) {
      if (_inFlight.contains(row.clientId)) continue;
      try {
        await send(row);
        sent++;
      } on Object catch (e) {
        if (!isRetryable(e)) {
          failed++;
        } else if (isNetworkError(e)) {
          break;
        }
      }
    }
    final kept = (await _queue.pending()).length;
    return (sent: sent, failed: failed, kept: kept);
  }

  static MealIn toMealIn(PendingMeal row) => MealIn(
    memberId: row.memberId,
    productId: row.productId,
    barcode: row.barcode,
    grams: row.grams,
    servings: row.servings,
    eatenAt: row.eatenAt.toUtc(),
    clientId: row.clientId,
  );
}
