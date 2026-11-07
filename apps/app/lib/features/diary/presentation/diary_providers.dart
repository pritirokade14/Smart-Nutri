import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/time/timezone_sync.dart';
import '../../home/presentation/home_screen.dart' show meProvider;
import '../../../core/storage/meal_queue.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/diary_repository.dart';
import '../data/meal_slots_repository.dart';

final diaryRepositoryProvider = Provider<DiaryRepository>((ref) {
  final api = ref.watch(apiClientProvider);
  return DiaryRepository(api.diary, ref.watch(mealsClientProvider));
});

final mealSlotsRepositoryProvider = Provider<MealSlotsRepository>(
  (ref) => MealSlotsRepository(ref.watch(apiClientProvider).mealSlots),
);

/// One diary day (null: the account's local today, as the API decides).
/// Reloads when the stored log changes. No automatic retry: the screen shows
/// the failure and the user retries.
final diaryDayProvider = FutureProvider.autoDispose
    .family<DiaryDayOut, String?>((ref, date) {
      ref.watch(mealsRevisionProvider);
      return ref.watch(diaryRepositoryProvider).day(date: date);
    }, retry: (_, _) => null);

/// The 7 days ending on [end] (null: today).
final diaryWeekProvider = FutureProvider.autoDispose
    .family<DiaryWeekOut, String?>((ref, end) {
      ref.watch(mealsRevisionProvider);
      return ref.watch(diaryRepositoryProvider).week(end: end);
    }, retry: (_, _) => null);

/// The member's meal slots. When it has not loaded (offline) the add-food
/// sheet hides its slot chips and the API picks the slot (Ruling E19).
final mealSlotsProvider = FutureProvider.autoDispose<MealSlotsOut>((ref) {
  ref.watch(mealsRevisionProvider);
  return ref.watch(mealSlotsRepositoryProvider).list();
}, retry: (_, _) => null);

/// Sends the device time zone once per app start after sign-in. Wraps the
/// signed-in shell.
class TimezoneSyncScope extends ConsumerStatefulWidget {
  const TimezoneSyncScope({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<TimezoneSyncScope> createState() => _TimezoneSyncScopeState();
}

class _TimezoneSyncScopeState extends ConsumerState<TimezoneSyncScope> {
  bool _done = false;

  void _run(MeOut me) {
    if (_done) return;
    _done = true;
    syncTimezone(me, ref.read(apiClientProvider).me);
  }

  @override
  Widget build(BuildContext context) {
    final me = ref.watch(meProvider).value;
    if (me != null) _run(me);
    return widget.child;
  }
}

/// `diary_day_viewed {}`: sent once when a Diary screen opens. No date, no
/// numbers.
void trackDiaryDayViewed(WidgetRef ref) =>
    ref.read(analyticsProvider).track('diary_day_viewed');

/// Where the next "I ate this" log from the search, barcode or label flows
/// goes: set by the add-food sheet, read by the portion sheet, cleared when
/// the user is back on the Diary.
class DiaryAddContext {
  const DiaryAddContext({
    required this.method,
    this.slotId,
    this.localDate,
    this.memberId,
  });

  /// The analytics `method` (`search`, `barcode`, `label`).
  final String method;
  final String? slotId;

  /// A past day, else null.
  final String? localDate;

  /// The member whose diary this is.
  final String? memberId;
}

class DiaryAddContextNotifier extends Notifier<DiaryAddContext?> {
  @override
  DiaryAddContext? build() => null;

  void set(DiaryAddContext c) => state = c;
  void clear() => state = null;
}

final diaryAddContextProvider =
    NotifierProvider<DiaryAddContextNotifier, DiaryAddContext?>(
      DiaryAddContextNotifier.new,
    );

/// Recent foods, the given slot's first.
final diaryRecentsProvider = FutureProvider.autoDispose
    .family<List<RecentItem>, String?>(
      (ref, slotId) =>
          ref.watch(diaryRepositoryProvider).recents(slotId: slotId),
      retry: (_, _) => null,
    );

/// Entries waiting on this phone.
final pendingEntriesProvider = StreamProvider.autoDispose<List<PendingMeal>>(
  (ref) => ref.watch(mealQueueProvider).watchPending(),
);
