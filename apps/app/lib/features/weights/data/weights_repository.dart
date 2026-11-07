import 'package:dio/dio.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../diary/domain/diary_dates.dart';
import '../../meals/data/meal_sync.dart' show isRetryable;

/// A failed weights call. [code] is the API `error.code`
/// (`weight_out_of_range`, `weight_needs_confirm`, `weight_not_found`, ...),
/// `network` when there was no response, or null. For `weight_needs_confirm`
/// [previousKg] is the last weigh-in, or null when the API hides it.
class WeightsFailure implements Exception {
  const WeightsFailure(this.code, [this.cause, this.previousKg]);

  final String? code;
  final Object? cause;
  final num? previousKg;

  bool get needsConfirm => code == 'weight_needs_confirm';

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      final code = apiErrorCode(e);
      num? previous;
      if (code == 'weight_needs_confirm' && e is DioException) {
        final details = parseErrorEnvelope(e.response?.data)?.error.details;
        if (details is Map && details['previous'] is num) {
          previous = details['previous'] as num;
        }
      }
      throw WeightsFailure(code, e, previous);
    }
  }

  @override
  String toString() => 'WeightsFailure($code)';
}

/// What [WeightsRepository.log] did.
sealed class WeighInResult {
  const WeighInResult();
}

class WeighInSaved extends WeighInResult {
  const WeighInSaved(this.weight);
  final WeightOut weight;
}

/// Kept on the phone (offline, 5xx or 429); sent later with the same
/// `client_id`.
class WeighInQueued extends WeighInResult {
  const WeighInQueued(this.clientId);
  final String clientId;
}

/// Wraps the generated `WeightsClient` and the offline weigh-in queue. It
/// only sends and shows what the API answers: the trend, the rate and the
/// projection are never worked out here.
class WeightsRepository {
  WeightsRepository(this._client, this._queue, {Uuid? uuid})
    : _uuid = uuid ?? const Uuid();

  final WeightsClient _client;
  final WeighInQueue _queue;
  final Uuid _uuid;

  Future<WeightsOut> list() =>
      WeightsFailure.guard(() => _client.weightsList());

  Future<WeightTrendOut> trend(Days days) =>
      WeightsFailure.guard(() => _client.weightsTrendGet(days: days));

  /// Saves the weigh-in of [date] (`2026-11-07`). Offline it is queued and
  /// [WeighInQueued] returned. `weight_needs_confirm` and every other refusal
  /// throw [WeightsFailure]; [confirmUnusual] sends the confirmation.
  Future<WeighInResult> log(
    String date,
    num weightKg, {
    bool confirmUnusual = false,
    String? clientId,
  }) async {
    final id = clientId ?? _uuid.v4();
    try {
      final out = await _client.weightsPut(
        day: parseDateKey(date)!,
        body: WeightIn(
          weightKg: weightKg,
          confirmUnusual: confirmUnusual,
          clientId: id,
        ),
      );
      return WeighInSaved(out);
    } on Object catch (e) {
      if (isRetryable(e)) {
        await _queue.addWeighIn(
          PendingWeighIn(
            clientId: id,
            localDate: date,
            weightKg: weightKg.toDouble(),
            confirmUnusual: confirmUnusual,
            status: WeighInStatus.pending,
            attempts: 0,
          ),
        );
        return WeighInQueued(id);
      }
      return WeightsFailure.guard<WeighInResult>(() => throw e);
    }
  }

  /// Online only. Works without `health_data` consent (erasing is always
  /// allowed).
  Future<void> delete(String date) => WeightsFailure.guard(
    () => _client.weightsDelete(day: parseDateKey(date)!),
  );

  /// Online only; terms consent is enough (erasing never needs
  /// `health_data`). Returns how many weigh-ins were deleted.
  Future<int> deleteAll() async =>
      (await WeightsFailure.guard(() => _client.weightsDeleteAll())).deleted;
}
