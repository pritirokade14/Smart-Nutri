import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../history/presentation/summary_display.dart';
import '../../meals/domain/meal_summary.dart';

/// Today's protein against the member's daily protein guide, exactly as the
/// API sent it (total, `limits.protein_target_g`, `protein_left_g`). The
/// target is a guide, never a need, and it never colours a verdict: the bar
/// uses the brand colour, and an unknown total is the grey "Not enough data"
/// chip (never green). Calories are shown without a target.
class ProteinProgress extends StatelessWidget {
  const ProteinProgress({super.key, required this.summary, this.onAddDetails});

  final MealSummary summary;

  /// Opens the member form to add weight and year of birth (no target yet).
  final VoidCallback? onAddDetails;

  static const noTargetKey = Key('protein-no-target');
  static const progressKey = Key('protein-progress');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final total = summary.totals.protein;
    final target = summary.limits.protein;
    final left = summary.proteinLeftG;
    final kcal = summary.totals.kcal;
    final band = shownBand(
      SummaryNutrient.protein,
      summary.bands.protein,
      total,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                total == null
                    ? l10n.summaryNothingLogged
                    : target == null
                    ? l10n.summaryTotalG(formatAmount(total))
                    : l10n.proteinProgress(
                        formatAmount(target),
                        formatAmount(total),
                      ),
                key: progressKey,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ),
            if (band != null) BandChip(band: band),
          ],
        ),
        if (total != null && target != null && target > 0) ...[
          const SizedBox(height: SnTokens.space2),
          ClipRRect(
            borderRadius: BorderRadius.circular(SnTokens.radiusFull),
            child: LinearProgressIndicator(
              value: (total / target).clamp(0, 1).toDouble(),
              minHeight: SnTokens.space2,
              color: c.brand,
              backgroundColor: c.muted,
            ),
          ),
        ],
        if (left != null && target != null)
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Text(
              l10n.proteinLeftToday(formatAmount(left)),
              style: theme.textTheme.bodyMedium,
            ),
          ),
        if (target == null)
          Padding(
            key: noTargetKey,
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SummaryNote(text: l10n.proteinNoTarget),
                if (onAddDetails != null)
                  TextButton.icon(
                    icon: const Icon(Icons.edit_outlined),
                    label: Text(l10n.membersEdit),
                    onPressed: onAddDetails,
                  ),
              ],
            ),
          ),
        if (kcal != null)
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Text(
              l10n.summaryKcalTotal(formatAmount(kcal)),
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
      ],
    );
  }
}
