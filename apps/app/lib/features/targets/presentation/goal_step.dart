import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/targets_format.dart';
import 'guide_draft.dart';

String directionLabel(AppLocalizations l10n, String direction) =>
    switch (direction) {
      'lose' => l10n.targetsDirectionLose,
      'gain' => l10n.targetsDirectionGain,
      _ => l10n.targetsDirectionMaintain,
    };

/// Direction, pace (the API's `rate_options`, never computed here), target
/// weight and the pregnancy question.
class GoalStep extends StatelessWidget {
  const GoalStep({
    super.key,
    required this.draft,
    required this.preview,
    required this.onChanged,
    this.notice,
    this.targetWeightError,
  });

  final GuideDraft draft;

  /// The latest `targets_preview`, for the pace chips and the default pace.
  final TargetsOut? preview;

  /// Called after an answer changes that needs a new preview.
  final VoidCallback onChanged;

  /// A neutral note, e.g. the underweight message.
  final String? notice;
  final String? targetWeightError;

  static Key directionKey(String d) => Key('guide-direction-$d');
  static Key rateKey(int index) => Key('guide-rate-$index');
  static const targetWeightKey = Key('guide-target-weight');
  static Key pregnancyKey(String v) => Key('guide-pregnancy-$v');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return ListenableBuilder(
      listenable: draft,
      builder: (context, _) {
        final options = preview?.rateOptions ?? const <RateOut>[];
        final current = draft.ratePct ?? preview?.rate?.pctBwPerWeek;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Wrap(
              spacing: SnTokens.space2,
              children: [
                for (final d in directionOptions)
                  ChoiceChip(
                    key: directionKey(d),
                    label: Text(directionLabel(l10n, d)),
                    selected: draft.direction == d,
                    onSelected: (_) {
                      draft.direction = d;
                      draft.ratePct = null;
                      draft.notify();
                      onChanged();
                    },
                  ),
              ],
            ),
            if (notice case final text?)
              Padding(
                padding: const EdgeInsets.only(top: SnTokens.space2),
                child: Text(
                  text,
                  key: const Key('guide-goal-notice'),
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: c.textSecondary,
                  ),
                ),
              ),
            if (draft.direction != 'maintain' && options.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space3),
              Text(l10n.targetsRateTitle, style: theme.textTheme.titleSmall),
              Wrap(
                spacing: SnTokens.space2,
                children: [
                  for (final (i, o) in options.indexed)
                    ChoiceChip(
                      key: rateKey(i),
                      label: Text(
                        // kg is null when numbers are hidden: the pace shows as a percent.
                        o.kgPerWeek == null
                            ? l10n.targetsRateOptionPct(
                                formatDecimal(o.pctBwPerWeek),
                              )
                            : l10n.targetsRateOption(
                                formatDecimal(o.kgPerWeek!),
                                formatDecimal(o.pctBwPerWeek),
                              ),
                      ),
                      selected: current == o.pctBwPerWeek,
                      onSelected: (_) {
                        draft.ratePct = o.pctBwPerWeek;
                        draft.notify();
                        onChanged();
                      },
                    ),
                ],
              ),
            ],
            const SizedBox(height: SnTokens.space3),
            TextField(
              key: targetWeightKey,
              controller: draft.targetWeight,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: InputDecoration(
                labelText: l10n.targetsTargetWeight,
                errorText: targetWeightError,
              ),
              onChanged: (_) => draft.notify(),
              onEditingComplete: onChanged,
            ),
            const SizedBox(height: SnTokens.space3),
            Text(
              l10n.targetsPregnancyQuestion,
              style: theme.textTheme.titleSmall,
            ),
            RadioGroup<String>(
              groupValue: draft.pregnancy,
              onChanged: (v) {
                if (v == null) return;
                draft.pregnancy = v;
                draft.notify();
                onChanged();
              },
              child: Column(
                children: [
                  for (final (value, label) in [
                    ('yes', l10n.targetsPregnancyYes),
                    ('no', l10n.targetsPregnancyNo),
                    ('prefer_not', l10n.targetsPregnancyPreferNot),
                  ])
                    RadioListTile<String>(
                      key: pregnancyKey(value),
                      contentPadding: EdgeInsets.zero,
                      value: value,
                      title: Text(label),
                    ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
