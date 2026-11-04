import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../auth/data/auth_repository.dart';
import '../data/meal_sync.dart';
import '../data/meals_repository.dart';

/// The on-device offline log queue (drift).
final mealQueueProvider = Provider<MealQueue>((ref) {
  final db = MealQueueDatabase.open();
  ref.onDispose(db.close);
  return DriftMealQueue(db);
});

/// Ends the session: the offline log is wiped first (a log belongs to the
/// account that made it), then the user is signed out. A failed wipe never
/// blocks the sign-out.
Future<void> signOutClearingQueue(AuthRepository auth, MealQueue queue) async {
  try {
    await queue.clearAll();
  } on Object {
    // Still sign out.
  }
  await auth.signOut();
}

final mealsClientProvider = Provider<MealsClient>(
  (ref) => ref.watch(apiClientProvider).meals,
);

final mealSyncProvider = Provider<MealSync>(
  (ref) =>
      MealSync(ref.watch(mealsClientProvider), ref.watch(mealQueueProvider)),
);

final mealsRepositoryProvider = Provider<MealsRepository>(
  (ref) => MealsRepository(
    ref.watch(mealsClientProvider),
    ref.watch(mealQueueProvider),
    ref.watch(mealSyncProvider),
  ),
);

/// Fires when the phone gets a network connection back.
final connectivityRegainedProvider = Provider<Stream<void>>(
  (ref) => Connectivity().onConnectivityChanged
      .where((r) => r.any((c) => c != ConnectivityResult.none))
      .map((_) {}),
);

/// Logs still waiting on this phone.
final pendingMealsCountProvider = StreamProvider<int>(
  (ref) => ref.watch(mealQueueProvider).watchPendingCount(),
);

/// Logs the API refused during a sync (shown once, then cleared).
final failedMealsCountProvider = StreamProvider<int>(
  (ref) => ref.watch(mealQueueProvider).watchFailedCount(),
);

/// Bumped whenever the stored log changes (a log, an undo, a sync), so the
/// history and summaries reload.
class MealsRevision extends Notifier<int> {
  @override
  int build() => 0;

  void bump() => state++;
}

final mealsRevisionProvider = NotifierProvider<MealsRevision, int>(
  MealsRevision.new,
);

/// Flushes the offline log queue on app start, on resume and when the
/// connection comes back. Wraps the signed-in shell.
class MealSyncScope extends ConsumerStatefulWidget {
  const MealSyncScope({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<MealSyncScope> createState() => _MealSyncScopeState();
}

class _MealSyncScopeState extends ConsumerState<MealSyncScope>
    with WidgetsBindingObserver {
  StreamSubscription<void>? _connectivity;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _connectivity = ref
        .read(connectivityRegainedProvider)
        .listen((_) => _flush(), onError: (Object _) {});
    _flush();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _flush();
  }

  Future<void> _flush() async {
    try {
      final result = await ref.read(mealSyncProvider).flush();
      if (mounted && (result.sent > 0 || result.failed > 0)) {
        ref.read(mealsRevisionProvider.notifier).bump();
      }
    } on Object {
      // The queue keeps every row; the next trigger tries again.
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _connectivity?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
