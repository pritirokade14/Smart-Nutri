import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../core/theme/verdict_colors.dart';
import '../../meals/domain/meal_summary.dart';
import '../../scan/domain/number_text.dart';

String nutrientLabel(AppLocalizations l10n, SummaryNutrient n) => switch (n) {
  SummaryNutrient.sugars => l10n.summaryNutrientSugarsG,
  SummaryNutrient.salt => l10n.summaryNutrientSaltG,
  SummaryNutrient.protein => l10n.summaryNutrientProteinG,
  SummaryNutrient.kcal => l10n.summaryNutrientEnergyKcal,
};

String bandLabel(AppLocalizations l10n, Band band) => switch (band) {
  Band.ok => l10n.summaryBandOk,
  Band.near => l10n.summaryBandNear,
  Band.over => l10n.summaryBandOver,
  Band.unknown => l10n.summaryBandUnknown,
};

/// Sugar and salt have limits, so they carry a band. Protein is progress
/// towards a target and kcal has no personal target: neither ever shows
/// "Within limit".
bool hasLimitBand(SummaryNutrient n) =>
    n == SummaryNutrient.sugars || n == SummaryNutrient.salt;

/// The band to show next to [total]: the API's band, except that an unknown
/// total is always "Not enough data" (never fine). Null means no band chip
/// (protein or kcal with a known total).
Band? shownBand(SummaryNutrient n, Band band, num? total) {
  if (total == null) return Band.unknown;
  return hasLimitBand(n) ? band : null;
}

/// Verdict tokens for a band: ok green, near amber, over red, unknown grey.
VerdictTone bandTone(SnColors c, Band band) => verdictTone(c, switch (band) {
  Band.ok => 'ok',
  Band.near => 'caution',
  Band.over => 'avoid',
  Band.unknown => 'unknown',
});

String formatAmount(num value) => formatForDisplay(value);

/// The band as a pill: verdict colour, an icon and the label, so it never
/// relies on colour alone.
class BandChip extends StatelessWidget {
  const BandChip({super.key, required this.band});

  final Band band;

  static IconData iconFor(Band band) => switch (band) {
    Band.ok => Icons.check_circle_rounded,
    Band.near => Icons.warning_rounded,
    Band.over => Icons.arrow_upward_rounded,
    Band.unknown => Icons.help_rounded,
  };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final tone = bandTone(SnColors.of(context), band);
    final label = bandLabel(l10n, band);
    return Semantics(
      label: label,
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: SnTokens.space2,
          vertical: SnTokens.space1,
        ),
        decoration: BoxDecoration(
          color: tone.color,
          borderRadius: BorderRadius.circular(SnTokens.radiusFull),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(iconFor(band), size: SnTokens.fontSizeMd, color: tone.onColor),
            const SizedBox(width: SnTokens.space1),
            Text(
              label,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: tone.onColor,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A small secondary-text note with an info icon.
class SummaryNote extends StatelessWidget {
  const SummaryNote({super.key, required this.text, this.icon});

  final String text;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: SnTokens.space2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon ?? Icons.info_outline_rounded,
            size: SnTokens.fontSizeMd,
            color: c.textSecondary,
          ),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Text(
              text,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
            ),
          ),
        ],
      ),
    );
  }
}
