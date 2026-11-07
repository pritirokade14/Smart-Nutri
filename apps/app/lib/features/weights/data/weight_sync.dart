// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../diary/domain/diary_dates.dart';
import '../../meals/data/meal_sync.dart' show isNetworkError, isRetryable;

/// Sends the offline weigh-ins. Each goes with its stored `client_id`, so a
/// retry after a timeout never stores it twice.
class WeighInSync {
  WeighInSync(this._client, this._queue);

  final WeightsClient _client;
  final WeighInQueue _queue;
  Future<int>? _running;

  /// Sends every queued weigh-in once; returns how many were stored. Stops at
  /// the first network failure. `weight_needs_confirm` marks the row for the
  /// user to check; any other refusal drops it from the queue view.
  Future<int> flush() => _running ??= _flush().whenComplete(() {
    _running = null;
  });

  Future<int> _flush() async {
    var sent = 0;
    for (final row in await _queue.pendingWeighIns()) {
      try {
        await _client.weightsPut(
          day: parseDateKey(row.localDate)!,
          body: WeightIn(
            weightKg: row.weightKg,
            confirmUnusual: row.confirmUnusual,
            clientId: row.clientId,
          ),
        );
        await _queue.removeWeighIn(row.clientId);
        sent++;
      } on Object catch (e) {
        if (isRetryable(e)) {
          await _queue.recordWeighInAttempt(row.clientId);
          if (isNetworkError(e)) break;
        } else if (apiErrorCode(e) == 'weight_needs_confirm') {
          await _queue.setWeighInStatus(
            row.clientId,
            WeighInStatus.needsConfirm,
          );
        } else {
          await _queue.setWeighInStatus(row.clientId, WeighInStatus.failed);
        }
      }
    }
    return sent;
  }
}
