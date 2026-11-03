import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../meals/domain/meal_summary.dart';
import '../../meals/presentation/meals_providers.dart';

/// The member whose history is shown; null until the user picks one (the
/// screen then uses the account holder).
class HistoryMember extends Notifier<String?> {
  @override
  String? build() => null;

  void select(String memberId) => state = memberId;
}

final historyMemberProvider = NotifierProvider<HistoryMember, String?>(
  HistoryMember.new,
);

typedef SummaryQuery = ({String memberId, SummaryPeriod period});

/// Reloads whenever the stored log changes. No automatic retry: the screen
/// shows the failure and the user retries explicitly.
final mealSummaryProvider = FutureProvider.autoDispose
    .family<MealSummary, SummaryQuery>((ref, q) {
      ref.watch(mealsRevisionProvider);
      return ref.watch(mealsRepositoryProvider).summary(q.memberId, q.period);
    }, retry: (_, _) => null);

/// A member's logs of the last 7 IST days, newest first.
final mealsListProvider = FutureProvider.autoDispose
    .family<List<MealOut>, String>((ref, memberId) {
      ref.watch(mealsRevisionProvider);
      return ref.watch(mealsRepositoryProvider).list(memberId);
    }, retry: (_, _) => null);

/// Whole-family counts for the weekly share.
final weekCountsProvider = FutureProvider.autoDispose<WeekCounts>((ref) {
  ref.watch(mealsRevisionProvider);
  return ref.watch(mealsRepositoryProvider).weekCounts();
}, retry: (_, _) => null);
