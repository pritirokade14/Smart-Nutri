import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import 'guide_draft.dart';

String activityLabel(AppLocalizations l10n, String level) => switch (level) {
  'light' => l10n.targetsActivityLight,
  'moderate' => l10n.targetsActivityModerate,
  'very' => l10n.targetsActivityVery,
  _ => l10n.targetsActivitySedentary,
};

String activityHint(AppLocalizations l10n, String level) => switch (level) {
  'light' => l10n.targetsActivityLightHint,
  'moderate' => l10n.targetsActivityModerateHint,
  'very' => l10n.targetsActivityVeryHint,
  _ => l10n.targetsActivitySedentaryHint,
};

/// Four cards with everyday examples.
class ActivityStep extends StatelessWidget {
  const ActivityStep({super.key, required this.draft});

  final GuideDraft draft;

  static Key levelKey(String level) => Key('guide-activity-$level');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    return ListenableBuilder(
      listenable: draft,
      builder: (context, _) => RadioGroup<String>(
        groupValue: draft.activity ?? '',
        onChanged: (v) {
          draft.activity = v;
          draft.notify();
        },
        child: Column(
          children: [
            for (final level in activityLevels)
              Card(
                color: draft.activity == level ? c.brandSoft : null,
                child: RadioListTile<String>(
                  key: levelKey(level),
                  value: level,
                  title: Text(activityLabel(l10n, level)),
                  subtitle: Text(activityHint(l10n, level)),
                ),
              ),
            const SizedBox(height: SnTokens.space2),
          ],
        ),
      ),
    );
  }
}
