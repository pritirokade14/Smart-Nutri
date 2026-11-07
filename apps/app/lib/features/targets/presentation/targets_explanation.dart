import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/targets_format.dart';

/// "How we got this": every value is the API's own (hidden values arrive as
/// null and their lines are left out, so no number leaks).
class TargetsExplanationTile extends StatelessWidget {
  const TargetsExplanationTile(this.targets, {super.key});

  final TargetsOut targets;

  static const tileKey = Key('targets-explanation');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final e = targets.explanation;
    if (e == null) return const SizedBox.shrink();
    final lines = <String>[
      if (e.bmrKcal != null) l10n.targetsHowBmr(formatWhole(l10n, e.bmrKcal!)),
      if (e.activityFactor != null)
        l10n.targetsHowActivity(formatDecimal(e.activityFactor!)),
      if (e.maintenanceKcal != null)
        l10n.targetsHowMaintenance(formatWhole(l10n, e.maintenanceKcal!)),
      if (e.adjustmentKcal != null)
        l10n.targetsHowAdjustment(formatWhole(l10n, e.adjustmentKcal!)),
      if (e.floorKcal != null)
        l10n.targetsHowFloor(formatWhole(l10n, e.floorKcal!)),
      // Where the weight came from; the API leaves it out under hidden macros.
      if (e.weightKgUsed != null &&
          e.weightSource == TargetsExplanationWeightSource.trend)
        l10n.targetsHowWeightTrend(formatDecimal(e.weightKgUsed!))
      else if (e.weightKgUsed != null &&
          e.weightSource == TargetsExplanationWeightSource.latest)
        l10n.targetsHowWeightLatest(formatDecimal(e.weightKgUsed!)),
      if (e.proteinGPerKg != null && e.proteinReferenceWeightKg != null)
        _protein(
          l10n,
          e.proteinBasis,
          formatDecimal(e.proteinGPerKg!),
          formatDecimal(e.proteinReferenceWeightKg!),
        ),
    ];
    return ExpansionTile(
      key: tileKey,
      tilePadding: EdgeInsets.zero,
      title: Text(l10n.targetsHowTitle),
      expandedCrossAxisAlignment: CrossAxisAlignment.start,
      childrenPadding: const EdgeInsets.only(bottom: SnTokens.space2),
      children: [
        for (final line in lines)
          Padding(
            padding: const EdgeInsets.only(bottom: SnTokens.space1),
            child: Text(line),
          ),
        TextButton(
          onPressed: () => context.push('/methodology'),
          child: Text(l10n.targetsHowSources),
        ),
      ],
    );
  }

  static String _protein(
    AppLocalizations l10n,
    TargetsExplanationProteinBasis basis,
    String perKg,
    String weight,
  ) => switch (basis) {
    TargetsExplanationProteinBasis.leanMass => l10n.targetsHowProteinLean(
      perKg,
      weight,
    ),
    TargetsExplanationProteinBasis.adjustedWeight =>
      l10n.targetsHowProteinAdjusted(perKg, weight),
    _ => l10n.targetsHowProtein(perKg, weight),
  };
}

/// The small grey "Pending clinician review" line.
class PendingReviewNote extends StatelessWidget {
  const PendingReviewNote({super.key});

  static const noteKey = Key('targets-pending-review');

  @override
  Widget build(BuildContext context) => Text(
    AppLocalizations.of(context).targetsPendingReview,
    key: noteKey,
    style: Theme.of(
      context,
    ).textTheme.bodySmall?.copyWith(color: SnColors.of(context).textSecondary),
  );
}
