import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../history/presentation/history_providers.dart';
import '../data/targets_repository.dart';

final targetsRepositoryProvider = Provider<TargetsRepository>(
  (ref) => TargetsRepository(ref.watch(apiClientProvider).targets),
);

/// Today's targets for the account holder, exactly as the API computed them.
/// No automatic retry: the card shows the failure and the user retries.
final todayTargetsProvider = FutureProvider.autoDispose<TargetsOut>(
  (ref) => ref.watch(targetsRepositoryProvider).get(),
  retry: (_, _) => null,
);

/// The account holder's saved guide settings, or null when none exist.
final goalSettingsProvider = FutureProvider.autoDispose<GoalSettingsOut?>(
  (ref) => ref.watch(targetsRepositoryProvider).settings(),
  retry: (_, _) => null,
);

/// "Skip, just log food" on the Today card hides it for this session only.
class TodayTargetsDismissed extends Notifier<bool> {
  @override
  bool build() => false;

  void dismiss() => state = true;
}

final todayTargetsDismissedProvider =
    NotifierProvider<TodayTargetsDismissed, bool>(TodayTargetsDismissed.new);

/// Reloads everything that shows a target or a hidden number: the targets,
/// the settings and every meal summary.
void refreshTargets(WidgetRef ref) {
  ref.invalidate(todayTargetsProvider);
  ref.invalidate(goalSettingsProvider);
  ref.invalidate(mealSummaryProvider);
  ref.invalidate(diaryDayProvider);
  ref.invalidate(diaryWeekProvider);
}
