import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../domain/targets_format.dart';
import 'flag_notes.dart';
import 'targets_explanation.dart';

/// The field name for a member field the API listed as missing.
String missingFieldLabel(AppLocalizations l10n, String field) =>
    switch (field) {
      'birth_year' => l10n.targetsFieldBirthYear,
      'sex' => l10n.targetsFieldSex,
      'height' || 'height_cm' => l10n.targetsFieldHeight,
      'weight' || 'weight_kg' => l10n.targetsFieldWeight,
      'activity' || 'activity_level' => l10n.targetsFieldActivity,
      'body_fat' || 'body_fat_pct' => l10n.targetsFieldBodyFat,
      _ => field,
    };

/// The text for a status that has no numbers, or null when [t] is ready.
String? statusMessage(AppLocalizations l10n, TargetsOut t) =>
    switch (t.status) {
      TargetsOutStatus.needsBodyData => l10n.targetsNeedsBodyData(
        t.missingFields.map((f) => missingFieldLabel(l10n, f)).join(', '),
      ),
      TargetsOutStatus.notAvailableMinor => l10n.targetsMinor,
      TargetsOutStatus.pausedPregnancy => l10n.targetsPregnancyPaused,
      _ => null,
    };

/// Calories, protein, fat and carbs as rows (never rings), exactly as the
/// API sent them. A value the API hid is left out and one note says so.
class TargetRows extends StatelessWidget {
  const TargetRows(this.targets, {super.key});

  final TargetsOut targets;

  static Key rowKey(String name) => Key('target-row-$name');
  static const hiddenKey = Key('target-hidden-note');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final t = targets;
    final rows = <(String, String, String)>[
      if (t.energyKcal != null)
        ('energy', l10n.targetsEnergy, kcalText(l10n, t.energyKcal!)),
      if (t.proteinG != null)
        ('protein', l10n.targetsProtein, gramsText(l10n, t.proteinG!)),
      if (t.fatG != null) ('fat', l10n.targetsFat, gramsText(l10n, t.fatG!)),
      if (t.carbsG != null)
        ('carbs', l10n.targetsCarbs, gramsText(l10n, t.carbsG!)),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final (name, label, value) in rows)
          Padding(
            key: rowKey(name),
            padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
                Text(value),
              ],
            ),
          ),
        if (t.numbersHidden.energy || t.numbersHidden.macros)
          Padding(
            key: hiddenKey,
            padding: const EdgeInsets.only(top: SnTokens.space1),
            child: Text(
              l10n.diaryHiddenNumbers,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SnColors.of(context).textSecondary,
              ),
            ),
          ),
      ],
    );
  }
}

/// Step 5: the preview, with its explanation, flag notes, the kidney note and
/// the disclaimers. Saving is the screen's button.
class GuideResultStep extends StatelessWidget {
  const GuideResultStep({super.key, required this.targets});

  final TargetsOut targets;

  static const kidneyNoteKey = Key('guide-kidney-note');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final message = statusMessage(l10n, targets);
    final ready = targets.status == TargetsOutStatus.ready;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (message != null)
          Text(message, key: const Key('guide-status-message')),
        if (ready) ...[
          TargetRows(targets),
          TargetsExplanationTile(targets),
          FlagNotes(targets),
          const SizedBox(height: SnTokens.space3),
          Text(
            l10n.proteinKidneyNote,
            key: kidneyNoteKey,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
          const SizedBox(height: SnTokens.space2),
          const PendingReviewNote(),
        ],
        DisclaimerFooter(text: l10n.diaryDisclaimer),
      ],
    );
  }
}
