import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/weight_sync.dart';
import '../data/weights_repository.dart';

/// The weigh-in queue lives in the same on-device database as the meal log.
final weighInQueueProvider = Provider<WeighInQueue>((ref) {
  final q = ref.watch(mealQueueProvider);
  if (q is! WeighInQueue) {
    throw StateError('The meal queue has no weigh-in queue');
  }
  return q as WeighInQueue;
});

final weightsClientProvider = Provider<WeightsClient>(
  (ref) => ref.watch(apiClientProvider).weights,
);

final weightsRepositoryProvider = Provider<WeightsRepository>(
  (ref) => WeightsRepository(
    ref.watch(weightsClientProvider),
    ref.watch(weighInQueueProvider),
  ),
);

final weighInSyncProvider = Provider<WeighInSync>(
  (ref) => WeighInSync(
    ref.watch(weightsClientProvider),
    ref.watch(weighInQueueProvider),
  ),
);

/// The trend for one range. No automatic retry: the screen shows the failure.
final weightTrendProvider = FutureProvider.autoDispose
    .family<WeightTrendOut, Days>(
      (ref, days) => ref.watch(weightsRepositoryProvider).trend(days),
      retry: (_, _) => null,
    );

/// The weigh-ins of the last 90 days (the API's default), oldest first.
final weightListProvider = FutureProvider.autoDispose<WeightsOut>(
  (ref) => ref.watch(weightsRepositoryProvider).list(),
  retry: (_, _) => null,
);

/// Weigh-ins waiting on this phone, or waiting for a check.
final pendingWeighInsProvider =
    StreamProvider.autoDispose<List<PendingWeighIn>>(
      (ref) => ref.watch(weighInQueueProvider).watchWeighIns(),
    );

/// Reloads the trend and the list (and the targets, which follow the
/// weight) after a weigh-in changed.
void refreshWeights(WidgetRef ref) {
  ref.invalidate(weightTrendProvider);
  ref.invalidate(weightListProvider);
  ref.read(mealsRevisionProvider.notifier).bump();
}
