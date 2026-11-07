import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/targets_format.dart';

/// The note for an API flag, or null for a flag this build does not know.
///
/// With hidden numbers there are no digits: `floor_applied` uses the copy
/// without the value when the API sent no `floor_kcal`, and
/// `carbs_below_reference` (its copy names a macro value) is left out while
/// macros are hidden.
String? flagMessage(AppLocalizations l10n, String flag, TargetsOut t) {
  switch (flag) {
    case 'underweight_maintenance':
      return l10n.targetsFlagUnderweightMaintenance;
    case 'rate_capped':
      return l10n.targetsFlagRateCapped;
    case 'deficit_capped':
      return l10n.targetsFlagDeficitCapped;
    case 'taper_active':
      return l10n.targetsFlagTaperActive;
    case 'goal_weight_reached':
      return l10n.targetsFlagGoalWeightReached;
    case 'floor_applied':
      final floor = t.explanation?.floorKcal;
      return floor == null || t.numbersHidden.energy
          ? l10n.targetsFlagFloorAppliedHidden
          : l10n.targetsFlagFloorApplied(formatWhole(l10n, floor));
    case 'floor_limits_deficit':
      return l10n.targetsFlagFloorLimitsDeficit;
    case 'protein_capped':
      return l10n.targetsFlagProteinCapped;
    case 'carbs_below_reference':
      return t.numbersHidden.macros
          ? null
          : l10n.targetsFlagCarbsBelowReference;
    case 'average_sex_reference':
      return l10n.targetsFlagAverageSexReference;
    case 'outside_equation_age_range':
      return l10n.targetsFlagOutsideEquationAgeRange;
  }
  return null;
}

/// The API's flags as neutral information notes (never the danger token).
class FlagNotes extends StatelessWidget {
  const FlagNotes(this.targets, {super.key});

  final TargetsOut targets;

  static Key noteKey(String flag) => Key('flag-note-$flag');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final flag in targets.flags)
          if (flagMessage(l10n, flag, targets) case final message?)
            Container(
              key: noteKey(flag),
              margin: const EdgeInsets.only(top: SnTokens.space2),
              padding: const EdgeInsets.all(SnTokens.space3),
              decoration: BoxDecoration(
                color: c.muted,
                borderRadius: BorderRadius.circular(SnTokens.radiusMd),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: SnTokens.fontSizeMd,
                    color: c.textSecondary,
                  ),
                  const SizedBox(width: SnTokens.space2),
                  Expanded(
                    child: Text(
                      message,
                      style: Theme.of(
                        context,
                      ).textTheme.bodySmall?.copyWith(color: c.textPrimary),
                    ),
                  ),
                ],
              ),
            ),
      ],
    );
  }
}
