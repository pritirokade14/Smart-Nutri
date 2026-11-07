import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/section_header.dart';
import '../../meals/domain/meal_summary.dart';
import 'summary_display.dart';

/// Today's totals for one member against their daily limits, with the bands
/// exactly as the API judged them. An unknown total reads "Not enough data".
class DaySummaryCard extends StatelessWidget {
  const DaySummaryCard({super.key, required this.summary});

  final MealSummary summary;

  static const incompleteNoteKey = Key('day-summary-incomplete');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final s = summary;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(
              title: l10n.summaryTitleDay,
              icon: Icons.today_rounded,
            ),
            if (!s.anyLogged)
              Text(l10n.summaryNothingLogged)
            else ...[
              for (final n in SummaryNutrient.values)
                _NutrientLine(
                  nutrient: n,
                  total: s.totals[n],
                  limit: s.limits[n],
                  band: s.bands[n],
                  hidden: s.isHidden(n),
                ),
              if (s.anyIncomplete)
                SummaryNote(
                  key: incompleteNoteKey,
                  text: l10n.summaryIncomplete,
                ),
              if (s.totals.sugars != null)
                SummaryNote(text: l10n.summarySugarNote),
              if (s.totals.kcal != null)
                SummaryNote(text: l10n.summaryKcalInfo),
            ],
            SummaryNote(
              text: l10n.summaryLimitsNote,
              icon: Icons.pending_actions_rounded,
            ),
            const DisclaimerFooter(),
          ],
        ),
      ),
    );
  }
}

class _NutrientLine extends StatelessWidget {
  const _NutrientLine({
    required this.nutrient,
    required this.total,
    required this.limit,
    required this.band,
    this.hidden = false,
  });

  final SummaryNutrient nutrient;
  final num? total;
  final num? limit;
  final Band band;

  /// The API hid this number: say so, never "Not enough data".
  final bool hidden;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final total = this.total;
    final limit = this.limit;
    final chip = hidden
        ? hiddenBand(nutrient, band)
        : shownBand(nutrient, band, total);
    String? value;
    String? note;
    if (hidden) {
      value = l10n.diaryHiddenNumbers;
    } else if (total != null) {
      final t = formatAmount(total);
      switch (nutrient) {
        case SummaryNutrient.sugars || SummaryNutrient.salt:
          value = limit == null
              ? l10n.historyItemAmount(t)
              : l10n.summaryTotalOfLimit(formatAmount(limit), t);
        case SummaryNutrient.protein:
          if (limit == null) {
            value = l10n.historyItemAmount(t);
            note = l10n.summaryNoProteinTarget;
          } else {
            value = l10n.summaryProteinOfTarget(formatAmount(limit), t);
          }
        case SummaryNutrient.kcal:
          value = l10n.summaryKcalTotal(t);
      }
    }
    return Container(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space2),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: c.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  nutrientLabel(l10n, nutrient),
                  style: theme.textTheme.titleSmall,
                ),
                if (value != null)
                  Text(
                    value,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontFeatures: const [FontFeature.tabularFigures()],
                    ),
                  ),
                if (note != null)
                  Text(
                    note,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: c.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
          if (chip != null) ...[
            const SizedBox(width: SnTokens.space2),
            BandChip(band: chip),
          ],
        ],
      ),
    );
  }
}
