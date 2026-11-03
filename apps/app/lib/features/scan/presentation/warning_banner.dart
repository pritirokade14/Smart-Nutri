import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/draft_warnings.dart';

/// Warnings shown with the strongest emphasis: the whole label is in doubt.
const _prominentCodes = {
  'low_confidence',
  'unreadable_field',
  'basis_mismatch',
};

/// The confirm-screen label for a draft field (`confirm.field.*` already
/// includes the unit), or null for a field the screen has no label for.
String? fieldLabel(AppLocalizations l10n, String field) => switch (field) {
  'energy_kcal' => l10n.confirmFieldEnergyKcal,
  'protein_g' => l10n.confirmFieldProteinG,
  'carbs_g' => l10n.confirmFieldCarbsG,
  'sugars_g' => l10n.confirmFieldSugarsG,
  'added_sugars_g' => l10n.confirmFieldAddedSugarsG,
  'fat_g' => l10n.confirmFieldFatG,
  'sat_fat_g' => l10n.confirmFieldSatFatG,
  'trans_fat_g' => l10n.confirmFieldTransFatG,
  'fiber_g' => l10n.confirmFieldFiberG,
  'salt_g' => l10n.confirmFieldSaltG,
  'sodium_mg' => l10n.confirmFieldSodiumMg,
  'serving_size_g' => l10n.confirmServingSize,
  'ingredients' => l10n.confirmIngredients,
  'allergen_statement' => l10n.confirmAllergenStatement,
  'may_contain_statement' => l10n.confirmMayContainStatement,
  'claims' => l10n.confirmClaims,
  'product_name' || 'name' => l10n.confirmName,
  'brand' => l10n.confirmBrand,
  'category' => l10n.confirmCategory,
  'sodium_unit' => l10n.confirmSodiumUnit,
  _ => null,
};

/// `warning.<code>`; an unknown code falls back to the general "check every
/// value" line, so no warning is ever silently dropped.
String warningText(AppLocalizations l10n, String code) => switch (code) {
  'implausible_value' => l10n.warningImplausibleValue,
  'per_100g_missing' => l10n.warningPer100gMissing,
  'basis_mismatch' => l10n.warningBasisMismatch,
  'per_serving_ignored' => l10n.warningPerServingIgnored,
  'energy_mismatch' => l10n.warningEnergyMismatch,
  'kcal_kj_mismatch' => l10n.warningKcalKjMismatch,
  'salt_sodium_mismatch' => l10n.warningSaltSodiumMismatch,
  'unit_unconfirmed' => l10n.warningUnitUnconfirmed,
  'low_confidence' => l10n.warningLowConfidence,
  'category_unknown' => l10n.warningCategoryUnknown,
  'category_check' => l10n.warningCategoryCheck,
  'unreadable_field' => l10n.warningUnreadableField,
  'upper_bound' => l10n.warningUpperBound,
  'derived_from_serving' => l10n.warningDerivedFromServing,
  _ => l10n.confirmSubtitle,
};

/// One inline `warnings[]` entry. Never green: warnings use the caution
/// colour, and the label-wide doubts (low confidence, unreadable values) are
/// drawn more prominently.
class WarningBanner extends StatelessWidget {
  const WarningBanner({super.key, required this.warning});

  final DraftWarning warning;

  bool get prominent => _prominentCodes.contains(warning.code);

  Color get color => SnTokens.verdictCaution;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final field = warning.field;
    final label = field == null ? null : fieldLabel(l10n, field);
    return Container(
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: prominent ? 0.16 : 0.08),
        border: Border.all(color: color, width: prominent ? 2 : 1),
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.warning_amber_rounded, color: color),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (label != null)
                  Text(
                    label,
                    style: theme.textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                Text(
                  warningText(l10n, warning.code),
                  style: prominent
                      ? theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        )
                      : theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
