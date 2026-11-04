import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../../core/l10n/app_localizations.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/theme/tokens.g.dart';
import '../../../../shared/widgets/states.dart';
import '../../../history/presentation/history_providers.dart';
import '../../../history/presentation/summary_display.dart';
import '../../../meals/data/meals_repository.dart';
import '../../../meals/domain/meal_summary.dart';
import '../../../members/presentation/members_providers.dart';
import '../../../protein/presentation/protein_progress.dart';
import 'card_frame.dart';

/// Today's `meals_summary` for the account holder, or nothing while the
/// members load (the card then shows a skeleton).
class _PrimaryDaySummary extends ConsumerWidget {
  const _PrimaryDaySummary({required this.builder});

  final Widget Function(MealSummary summary, String memberId) builder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    final primary = members.value?.where((m) => m.isPrimary).firstOrNull;
    if (primary == null) {
      return members.hasError
          ? ErrorState(
              message: localizedErrorCode(l10n, null),
              onRetry: () => ref.invalidate(membersProvider),
            )
          : const LoadingSkeleton(lines: 2);
    }
    final day = (memberId: primary.id, period: SummaryPeriod.day);
    return ref
        .watch(mealSummaryProvider(day))
        .when(
          loading: () => const LoadingSkeleton(lines: 2),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is MealsFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(mealSummaryProvider(day)),
          ),
          data: (s) => builder(s, primary.id),
        );
  }
}

/// Today's sugar and salt against the daily limits, with the API's bands
/// (an unknown total is the grey "Not enough data", never green).
class TodaySugarSaltCard extends StatelessWidget {
  const TodaySugarSaltCard({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return HomeCardFrame(
      title: l10n.homeCardsTodaySugarSaltTitle,
      icon: Icons.today_rounded,
      child: _PrimaryDaySummary(
        builder: (s, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (final n in [SummaryNutrient.sugars, SummaryNutrient.salt])
              _LimitLine(
                nutrient: n,
                total: s.totals[n],
                limit: s.limits[n],
                band: s.bands[n],
              ),
          ],
        ),
      ),
    );
  }
}

class _LimitLine extends StatelessWidget {
  const _LimitLine({
    required this.nutrient,
    required this.total,
    required this.limit,
    required this.band,
  });

  final SummaryNutrient nutrient;
  final num? total;
  final num? limit;
  final Band band;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final total = this.total;
    final limit = this.limit;
    final chip = shownBand(nutrient, band, total);
    final value = total == null
        ? null
        : limit == null
        ? l10n.summaryTotalG(formatAmount(total))
        : l10n.summaryTotalOfLimit(formatAmount(limit), formatAmount(total));
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  nutrientLabel(l10n, nutrient),
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                if (value != null) Text(value),
              ],
            ),
          ),
          if (chip != null) BandChip(band: chip),
        ],
      ),
    );
  }
}

/// Today's protein against the daily protein guide (see [ProteinProgress]).
class TodayProteinCard extends StatelessWidget {
  const TodayProteinCard({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return HomeCardFrame(
      title: l10n.homeCardsTodayProteinTitle,
      icon: Icons.fitness_center_rounded,
      child: _PrimaryDaySummary(
        builder: (s, memberId) => ProteinProgress(
          summary: s,
          onAddDetails: () => context.push('/family/$memberId'),
        ),
      ),
    );
  }
}
