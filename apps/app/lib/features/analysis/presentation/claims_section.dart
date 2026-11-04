import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/section_header.dart';
import '../domain/report.dart';

/// `claim.<code>`, or null for a claim this build has no label for.
String? claimLabel(AppLocalizations l10n, String code) => switch (code) {
  'no_added_sugar' => l10n.claimNoAddedSugar,
  'sugar_free' => l10n.claimSugarFree,
  'low_sugar' => l10n.claimLowSugar,
  'low_fat' => l10n.claimLowFat,
  'low_sodium' => l10n.claimLowSodium,
  'high_protein' => l10n.claimHighProtein,
  'source_of_protein' => l10n.claimSourceOfProtein,
  'no_refined_sugar' => l10n.claimNoRefinedSugar,
  'diabetic_friendly' => l10n.claimDiabeticFriendly,
  'protein_amount' => l10n.claimProteinAmount,
  'whey_only' => l10n.claimWheyOnly,
  'whey_protein' => l10n.claimWheyProtein,
  _ => null,
};

String _verdictText(AppLocalizations l10n, String verdict) => switch (verdict) {
  'supported' => l10n.claimVerdictSupported,
  'contradicted' => l10n.claimVerdictContradicted,
  _ => l10n.claimVerdictUnverifiable,
};

// Latin digits in every locale, as for member reasons.
final _latinNumbers = NumberFormat.decimalPattern('en');

/// `claim_reason.<code>` with its params, or null when this build does not
/// know the code or the params do not fit (then no reason line is shown).
String? claimReasonText(AppLocalizations l10n, ClaimCheck check) {
  final p = check.params;
  String? number(String k) =>
      p[k] is num ? _latinNumbers.format(p[k]! as num) : null;
  String? list(String k) {
    final v = p[k];
    if (v is! List || v.isEmpty || v.any((e) => e is! String)) return null;
    return v.cast<String>().join(', ');
  }

  String? nutrient(String k) => switch (p[k]) {
    'energy_kcal' => l10n.nutrientEnergyKcal,
    'protein_g' => l10n.nutrientProteinG,
    'carbs_g' => l10n.nutrientCarbsG,
    'sugars_g' => l10n.nutrientSugarsG,
    'fat_g' => l10n.nutrientFatG,
    'sat_fat' => l10n.nutrientSatFat,
    'salt' => l10n.nutrientSalt,
    'sodium_mg' => l10n.nutrientSodiumMg,
    'serving_size_g' => l10n.nutrientServingSizeG,
    _ => null,
  };

  return switch (check.reasonCode) {
    'ok' => l10n.claimReasonOk,
    'ingredients_unknown' => l10n.claimReasonIngredientsUnknown,
    'no_standard' => l10n.claimReasonNoStandard,
    'exceeds_limit' => switch ((number('limit'), number('value'))) {
      (final limit?, final value?) => l10n.claimReasonExceedsLimit(
        limit,
        value,
      ),
      _ => null,
    },
    'below_minimum' => switch ((number('limit'), number('value'))) {
      (final limit?, final value?) => l10n.claimReasonBelowMinimum(
        limit,
        value,
      ),
      _ => null,
    },
    'nutrient_missing' => switch (nutrient('nutrient')) {
      final n? => l10n.claimReasonNutrientMissing(n),
      null => null,
    },
    'added_sugar_ingredient' => switch (list('ingredients')) {
      final i? => l10n.claimReasonAddedSugarIngredient(i),
      null => null,
    },
    'refined_sugar_ingredient' => switch (list('ingredients')) {
      final i? => l10n.claimReasonRefinedSugarIngredient(i),
      null => null,
    },
    'below_claimed' => switch ((
      number('value'),
      number('claimed'),
      p['basis'],
    )) {
      (final value?, final claimed?, final String basis) =>
        l10n.claimReasonBelowClaimed(basis, claimed, value),
      _ => null,
    },
    'other_protein_source' => switch (list('ingredients')) {
      final i? => l10n.claimReasonOtherProteinSource(i),
      null => null,
    },
    'whey_not_listed' => l10n.claimReasonWheyNotListed,
    _ => null,
  };
}

/// "Claims on the label, checked by SmartNutri": each front-of-pack claim
/// with the API's check result. Shows nothing when there is nothing to show.
class ClaimsSection extends StatelessWidget {
  const ClaimsSection({super.key, required this.checks});

  final List<ClaimCheck> checks;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final shown = [
      for (final c in checks)
        if (claimLabel(l10n, c.claim) case final label?)
          (check: c, label: label),
    ];
    if (shown.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.productClaimsHeading,
          icon: Icons.fact_check_outlined,
        ),
        for (final s in shown) ...[
          _ClaimTile(check: s.check, label: s.label),
          const SizedBox(height: SnTokens.space2),
        ],
      ],
    );
  }
}

class _ClaimTile extends StatelessWidget {
  const _ClaimTile({required this.check, required this.label});

  final ClaimCheck check;
  final String label;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    // A claim check is not a member verdict: a supported claim stays
    // neutral (never green), a contradicted one is flagged amber and an
    // unverifiable one is grey.
    final (icon, iconColor) = switch (check.verdict) {
      'supported' => (Icons.check_rounded, c.textSecondary),
      'contradicted' => (Icons.warning_rounded, c.verdictCaution),
      _ => (Icons.help_rounded, c.verdictUnknown),
    };
    final reason = claimReasonText(l10n, check);
    return Container(
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: c.surface,
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
        border: Border.all(color: c.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: iconColor, size: SnTokens.fontSizeXl),
          const SizedBox(width: SnTokens.space3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.productLabelSays(label),
                  style: theme.textTheme.titleSmall,
                ),
                Text(
                  _verdictText(l10n, check.verdict),
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (reason != null)
                  Text(
                    reason,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: c.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
