import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// The Nutri-Score the API calculated, as an A–E strip with the grade
/// raised, always labelled "calculated by SmartNutri" (never an FSSAI
/// rating). With no grade it says there was not enough label data.
class NutriScoreChip extends StatelessWidget {
  const NutriScoreChip({
    super.key,
    required this.grade,
    this.notScoredSupplement = false,
  });

  /// `report.nutriscore.reason == not_scored_supplement`: no grade is
  /// calculated for supplements, which the chip says instead of "not enough
  /// data".
  final bool notScoredSupplement;

  static const gradeTileKey = Key('nutriscore-grade-tile');
  static const _grades = ['A', 'B', 'C', 'D', 'E'];

  /// A–E from the API, or null.
  final String? grade;

  static Color gradeColor(String grade) => switch (grade) {
    'A' => SnTokens.gradeA,
    'B' => SnTokens.gradeB,
    'C' => SnTokens.gradeC,
    'D' => SnTokens.gradeD,
    _ => SnTokens.gradeE,
  };

  /// Whichever of the two text tokens contrasts more with [background].
  static Color onGrade(Color background) =>
      _contrast(background, SnTokens.textPrimary) >=
          _contrast(background, SnTokens.surfaceDefault)
      ? SnTokens.textPrimary
      : SnTokens.surfaceDefault;

  static double _contrast(Color a, Color b) {
    final la = a.computeLuminance() + 0.05;
    final lb = b.computeLuminance() + 0.05;
    return la > lb ? la / lb : lb / la;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final grade = this.grade;
    if (grade == null || !_grades.contains(grade)) {
      return Row(
        children: [
          Icon(Icons.info_outline_rounded, color: c.textSecondary),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Text(
              notScoredSupplement && grade == null
                  ? l10n.nutriscoreNotScoredSupplement
                  : l10n.nutriscoreInsufficientData,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
        ],
      );
    }
    const small = SnTokens.space5 + SnTokens.space1;
    const big = SnTokens.space7 - SnTokens.space1;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Semantics(
          label: l10n.resultGrade(grade),
          excludeSemantics: true,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              for (final g in _grades)
                if (g == grade)
                  Container(
                    key: gradeTileKey,
                    width: big,
                    height: big,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: gradeColor(g),
                      borderRadius: BorderRadius.circular(SnTokens.radiusMd),
                      border: Border.all(color: c.surface, width: 3),
                      boxShadow: [
                        BoxShadow(
                          color: c.textPrimary.withValues(alpha: 0.18),
                          blurRadius: SnTokens.elevationHigh,
                          offset: const Offset(0, SnTokens.elevationLow),
                        ),
                      ],
                    ),
                    child: Text(
                      g,
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: onGrade(gradeColor(g)),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  )
                else
                  Container(
                    width: small,
                    height: small,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: gradeColor(g).withValues(alpha: 0.35),
                      borderRadius: BorderRadius.circular(SnTokens.radiusSm),
                    ),
                    child: Text(
                      g,
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: c.textPrimary.withValues(alpha: 0.7),
                      ),
                    ),
                  ),
            ],
          ),
        ),
        const SizedBox(height: SnTokens.space2),
        Text(
          l10n.nutriscoreCalculatedBy,
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
      ],
    );
  }
}

/// A compact Nutri-Score tile for lists (search hits, alternatives, compare
/// columns). Same colours as [NutriScoreChip]; with no grade it shows a
/// neutral dash. The surrounding screen says "calculated by SmartNutri".
class NutriScoreBadge extends StatelessWidget {
  const NutriScoreBadge({super.key, required this.grade});

  /// A–E from the API, or null.
  final String? grade;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final grade = this.grade;
    final known = grade != null && NutriScoreChip._grades.contains(grade);
    final color = known ? NutriScoreChip.gradeColor(grade) : c.muted;
    return Semantics(
      label: known ? l10n.resultGrade(grade) : l10n.nutriscoreInsufficientData,
      excludeSemantics: true,
      child: Container(
        width: SnTokens.space6 + SnTokens.space1,
        height: SnTokens.space6 + SnTokens.space1,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(SnTokens.radiusSm),
        ),
        child: Text(
          known ? grade : '–',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            color: known ? NutriScoreChip.onGrade(color) : c.textSecondary,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}
