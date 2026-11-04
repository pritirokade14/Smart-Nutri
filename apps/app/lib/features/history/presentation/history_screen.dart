import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/share/share_sheet.dart';
import '../../../shared/share/share_text.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/nutri_score_chip.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/data/meals_repository.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/members_providers.dart';
import '../../scan/domain/number_text.dart';
import 'day_summary_card.dart';
import 'history_providers.dart';
import 'weekly_dashboard.dart';

/// "You" for the account holder, else the name, else the relation.
String memberOutLabel(AppLocalizations l10n, MemberOut m) {
  if (m.isPrimary) return l10n.resultYou;
  final name = m.name.trim();
  return name.isNotEmpty ? name : shareRelation(l10n, m.relation.json);
}

String _failureText(AppLocalizations l10n, Object e) =>
    localizedErrorCode(l10n, switch (e) {
      MealsFailure(:final code) => code,
      MembersFailure(:final code) => code,
      _ => null,
    });

/// History tab: per member, today's totals and the last 7 IST days against
/// their limits (bands from the API), the logged items, and the weekly
/// family share.
class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.historyTitle),
        actions: [
          IconButton(
            tooltip: l10n.searchTitle,
            icon: const Icon(Icons.search_rounded),
            onPressed: () => context.push('/search'),
          ),
        ],
      ),
      body: members.when(
        skipLoadingOnRefresh: false,
        loading: () => const SingleChildScrollView(
          padding: EdgeInsets.all(SnTokens.space4),
          child: LoadingSkeleton(card: true, lines: 4),
        ),
        error: (e, _) => Center(
          child: SingleChildScrollView(
            child: ErrorState(
              message: _failureText(l10n, e),
              onRetry: () => ref.invalidate(membersProvider),
            ),
          ),
        ),
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: EmptyState(
                icon: Icons.history_rounded,
                title: l10n.historyEmpty,
                body: l10n.historyBody,
              ),
            );
          }
          final picked = ref.watch(historyMemberProvider);
          final member =
              list.where((m) => m.id == picked).firstOrNull ??
              list.where((m) => m.isPrimary).firstOrNull ??
              list.first;
          return _HistoryBody(members: list, member: member);
        },
      ),
    );
  }
}

class _HistoryBody extends ConsumerWidget {
  const _HistoryBody({required this.members, required this.member});

  final List<MemberOut> members;
  final MemberOut member;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final day = (memberId: member.id, period: SummaryPeriod.day);
    final week = (memberId: member.id, period: SummaryPeriod.week);
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(mealSyncProvider).flush();
        ref.read(mealsRevisionProvider.notifier).bump();
      },
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space4,
          SnTokens.space2,
          SnTokens.space4,
          SnTokens.space6,
        ),
        children: [
          const _SyncBanner(),
          if (members.length > 1) ...[
            Text(
              l10n.historyMember,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: SnTokens.space2),
            Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space2,
              children: [
                for (final m in members)
                  ChoiceChip(
                    label: Text(memberOutLabel(l10n, m)),
                    selected: m.id == member.id,
                    onSelected: (_) =>
                        ref.read(historyMemberProvider.notifier).select(m.id),
                  ),
              ],
            ),
            const SizedBox(height: SnTokens.space4),
          ],
          ref
              .watch(mealSummaryProvider(day))
              .when(
                skipLoadingOnRefresh: false,
                loading: () => const LoadingSkeleton(card: true, lines: 2),
                error: (e, _) => ErrorState(
                  message: _failureText(l10n, e),
                  onRetry: () => ref.invalidate(mealSummaryProvider(day)),
                ),
                data: (s) => DaySummaryCard(summary: s),
              ),
          const SizedBox(height: SnTokens.space4),
          ref
              .watch(mealSummaryProvider(week))
              .when(
                skipLoadingOnRefresh: false,
                loading: () => const LoadingSkeleton(card: true, lines: 2),
                error: (e, _) => ErrorState(
                  message: _failureText(l10n, e),
                  onRetry: () => ref.invalidate(mealSummaryProvider(week)),
                ),
                data: (s) => WeeklyDashboard(summary: s),
              ),
          const SizedBox(height: SnTokens.space5),
          SectionHeader(
            title: l10n.historyThisWeek,
            icon: Icons.restaurant_menu_rounded,
          ),
          _MealList(memberId: member.id),
          const SizedBox(height: SnTokens.space4),
          const _ShareWeekButton(),
        ],
      ),
    );
  }
}

/// Logs still on the phone, and logs the API refused during a sync.
class _SyncBanner extends ConsumerWidget {
  const _SyncBanner();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final pending = ref.watch(pendingMealsCountProvider).value ?? 0;
    final failed = ref.watch(failedMealsCountProvider).value ?? 0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (pending > 0)
          Container(
            margin: const EdgeInsets.only(bottom: SnTokens.space3),
            padding: const EdgeInsets.all(SnTokens.space3),
            decoration: BoxDecoration(
              color: c.muted,
              borderRadius: BorderRadius.circular(SnTokens.radiusMd),
            ),
            child: Row(
              children: [
                Icon(Icons.cloud_upload_outlined, color: c.textSecondary),
                const SizedBox(width: SnTokens.space2),
                Expanded(child: Text(l10n.mealsQueuedOffline)),
              ],
            ),
          ),
        if (failed > 0)
          Padding(
            padding: const EdgeInsets.only(bottom: SnTokens.space3),
            child: InlineErrorBanner(
              message: l10n.mealsSyncFailed,
              action: TextButton(
                onPressed: () => ref.read(mealQueueProvider).clearFailed(),
                child: Text(MaterialLocalizations.of(context).okButtonLabel),
              ),
            ),
          ),
      ],
    );
  }
}

class _MealList extends ConsumerWidget {
  const _MealList({required this.memberId});

  final String memberId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(mealsListProvider(memberId))
        .when(
          skipLoadingOnRefresh: false,
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: _failureText(l10n, e),
            onRetry: () => ref.invalidate(mealsListProvider(memberId)),
          ),
          data: (meals) {
            if (meals.isEmpty) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: SnTokens.space3),
                child: Text(l10n.historyEmpty),
              );
            }
            // Grouped by the phone's calendar day, newest first (as sent).
            final now = DateTime.now();
            final dayFormat = DateFormat.MMMEd(l10n.localeName)
              ..useNativeDigits = false;
            String? last;
            final children = <Widget>[];
            for (final m in meals) {
              final local = m.eatenAt.toLocal();
              final isToday =
                  local.year == now.year &&
                  local.month == now.month &&
                  local.day == now.day;
              final header = isToday
                  ? l10n.historyToday
                  : dayFormat.format(local);
              if (header != last) {
                last = header;
                children.add(
                  Padding(
                    padding: const EdgeInsets.only(
                      top: SnTokens.space3,
                      bottom: SnTokens.space1,
                    ),
                    child: Text(
                      header,
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                  ),
                );
              }
              children.add(_MealTile(meal: m));
            }
            // Grades are calculated by us, never an official rating: say so
            // once under the list, only when a grade is shown.
            if (meals.any((m) => m.grade != null)) {
              children.add(
                Padding(
                  padding: const EdgeInsets.only(top: SnTokens.space1),
                  child: Text(
                    l10n.nutriscoreCalculatedBy,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SnColors.of(context).textSecondary,
                    ),
                  ),
                ),
              );
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: children,
            );
          },
        );
  }
}

class _MealTile extends ConsumerWidget {
  const _MealTile({required this.meal});

  final MealOut meal;

  Future<void> _remove(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(l10n.historyRemoveConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(material.cancelButtonLabel),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.historyRemove),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(mealsRepositoryProvider).delete(meal.id);
      ref.read(mealsRevisionProvider.notifier).bump();
    } on MealsFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final barcode = meal.barcode;
    final time = DateFormat('HH:mm').format(meal.eatenAt.toLocal());
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space3,
          SnTokens.space2,
          SnTokens.space1,
          SnTokens.space2,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                NutriScoreBadge(grade: meal.grade?.json),
                const SizedBox(width: SnTokens.space3),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(meal.productName, style: theme.textTheme.titleSmall),
                      Text(
                        '${l10n.historyItemAmount(formatForDisplay(meal.grams))} · $time',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: c.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  key: Key('meal-remove-${meal.id}'),
                  tooltip: l10n.historyRemove,
                  icon: const Icon(Icons.delete_outline_rounded),
                  onPressed: () => _remove(context, ref),
                ),
              ],
            ),
            if (meal.attribution != null && barcode != null)
              OffAttribution(barcode: barcode),
          ],
        ),
      ),
    );
  }
}

class _ShareWeekButton extends ConsumerStatefulWidget {
  const _ShareWeekButton();

  @override
  ConsumerState<_ShareWeekButton> createState() => _ShareWeekButtonState();
}

class _ShareWeekButtonState extends ConsumerState<_ShareWeekButton> {
  bool _busy = false;

  Future<void> _open() async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _busy = true);
    try {
      final counts = await ref.read(mealsRepositoryProvider).weekCounts();
      if (!mounted) return;
      setState(() => _busy = false);
      await showWeeklyShareSheet(
        context,
        scans: counts.scans,
        logged: counts.logged,
        url: shareUrlFor(ref, l10n.localeName),
      );
    } on MealsFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return SecondaryButton(
      label: l10n.shareWeeklyButton,
      icon: Icons.ios_share_rounded,
      busy: _busy,
      onPressed: _open,
    );
  }
}
