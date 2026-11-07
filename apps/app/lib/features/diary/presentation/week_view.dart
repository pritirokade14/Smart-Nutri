import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/share/share_sheet.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/data/meals_repository.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../targets/domain/targets_format.dart';
import '../../targets/presentation/targets_explanation.dart';
import '../data/diary_repository.dart';
import '../domain/diary_dates.dart';
import 'diary_providers.dart';

/// The seven days ending on [end] (null: today): energy bars against each
/// day's own target line, from the API's `progress`. No rating, no streak.
class WeekView extends ConsumerWidget {
  const WeekView({super.key, this.end});

  final String? end;

  static Key tileKey(String date) => Key('week-day-$date');
  static Key partialKey(String date) => Key('week-partial-$date');
  static Key incompleteKey(String date) => Key('week-incomplete-$date');
  static const averageKey = Key('week-average');
  static const proteinDaysKey = Key('week-protein-days');
  static const shareKey = Key('week-share');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(diaryWeekProvider(end))
        .when(
          skipLoadingOnRefresh: false,
          loading: () => const Padding(
            padding: EdgeInsets.all(SnTokens.space4),
            child: LoadingSkeleton(card: true, lines: 4),
          ),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is DiaryFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(diaryWeekProvider(end)),
          ),
          data: (w) => _WeekBody(week: w),
        );
  }
}

class _WeekBody extends StatelessWidget {
  const _WeekBody({required this.week});

  final DiaryWeekOut week;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final macrosHidden = week.numbersHidden.macros;
    final energyHidden = week.numbersHidden.energy;
    final anyTarget = week.days.any((d) => d.targets != null);
    final a = week.averages;
    final inc = week.averagesIncomplete;
    // Hidden: no averages and no protein-days line at all (the API still
    // sends protein_met_days under hide_all).
    final showAverages = !macrosHidden && week.averagedDays > 0;
    final lines = <(String, num?, bool, bool)>[
      (l10n.targetsEnergy, a.energyKcal, inc.energyKcal, true),
      (l10n.targetsProtein, a.proteinG, inc.proteinG, false),
      (l10n.targetsCarbs, a.carbsG, inc.carbsG, false),
      (l10n.targetsFat, a.fatG, inc.fatG, false),
    ];
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space4,
        SnTokens.space2,
        SnTokens.space4,
        SnTokens.space6,
      ),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(SnTokens.space3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final d in week.days) Expanded(child: _DayColumn(tile: d)),
              ],
            ),
          ),
        ),
        const SizedBox(height: SnTokens.space3),
        if (showAverages) ...[
          Text(
            l10n.diaryWeekAverage(week.averagedDays),
            key: WeekView.averageKey,
            style: theme.textTheme.titleSmall,
          ),
          for (final (label, value, incomplete, isEnergy) in lines)
            if (value != null && !(isEnergy && energyHidden))
              Padding(
                padding: const EdgeInsets.only(top: SnTokens.space1),
                child: Row(
                  children: [
                    Expanded(child: Text(label)),
                    // A lower bound (some day lacked the value): grey, with
                    // the "may be higher" note.
                    Text(
                      isEnergy ? kcalText(l10n, value) : gramsText(l10n, value),
                      style: TextStyle(
                        color: incomplete ? c.textSecondary : null,
                      ),
                    ),
                    if (incomplete)
                      Tooltip(
                        message: l10n.diaryIncomplete,
                        child: Icon(
                          Icons.info_outline_rounded,
                          size: SnTokens.fontSizeMd,
                          color: c.textSecondary,
                          semanticLabel: l10n.diaryIncomplete,
                        ),
                      ),
                  ],
                ),
              ),
          if (anyTarget)
            Padding(
              padding: const EdgeInsets.only(top: SnTokens.space2),
              child: Text(
                l10n.diaryWeekProteinDays(
                  week.averagedDays.toString(),
                  week.proteinMetDays.toString(),
                ),
                key: WeekView.proteinDaysKey,
              ),
            ),
        ],
        const SizedBox(height: SnTokens.space3),
        const _ShareWeekButton(),
        const SizedBox(height: SnTokens.space3),
        if (anyTarget) const Center(child: PendingReviewNote()),
        DisclaimerFooter(text: l10n.diaryDisclaimer),
      ],
    );
  }
}

class _DayColumn extends StatelessWidget {
  const _DayColumn({required this.tile});

  final DayTile tile;

  static const _barArea = 96.0;

  /// The bar area shows 0 to 125% of the day's own target; the line is the
  /// target itself.
  static const _scale = 1.25;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final date = dateKey(tile.date);
    final progress = tile.progress?.energyKcal;
    final logged = tile.items > 0;
    final incomplete = logged && tile.incomplete.energyKcal;
    final fill = progress == null
        ? null
        : (progress.toDouble().clamp(0.0, _scale) / _scale);
    final label = DateFormat.E(
      l10n.localeName,
    ).format(DateTime(tile.date.year, tile.date.month, tile.date.day));
    return Column(
      key: WeekView.tileKey(date),
      children: [
        SizedBox(
          height: _barArea,
          child: Stack(
            alignment: Alignment.bottomCenter,
            children: [
              if (tile.targets != null)
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: _barArea / _scale,
                  child: Container(height: 1, color: c.borderStrong),
                ),
              Container(
                width: 16,
                height: (fill ?? (logged ? 0.08 : 0)) * _barArea,
                decoration: BoxDecoration(
                  // Brand for a known value; grey when it is unknown.
                  color: incomplete || fill == null ? c.borderStrong : c.brand,
                  borderRadius: BorderRadius.circular(SnTokens.radiusSm),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: SnTokens.space1),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
        SizedBox(
          height: 20,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (tile.partialLogged)
                Tooltip(
                  message: l10n.diaryPartialBadge,
                  child: Icon(
                    Icons.timelapse_rounded,
                    key: WeekView.partialKey(date),
                    size: 14,
                    color: c.textSecondary,
                    semanticLabel: l10n.diaryPartialBadge,
                  ),
                ),
              if (incomplete)
                Tooltip(
                  message: l10n.diaryIncomplete,
                  child: Icon(
                    Icons.info_outline_rounded,
                    key: WeekView.incompleteKey(date),
                    size: 14,
                    color: c.textSecondary,
                    semanticLabel: l10n.diaryIncomplete,
                  ),
                ),
            ],
          ),
        ),
      ],
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
      buttonKey: WeekView.shareKey,
      label: l10n.diaryShareWeek,
      icon: Icons.ios_share_rounded,
      busy: _busy,
      onPressed: _open,
    );
  }
}
