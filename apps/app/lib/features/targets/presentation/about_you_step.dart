import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../members/domain/member.dart';
import '../../members/presentation/member_labels.dart';
import 'guide_draft.dart';

/// Birth year, sex, height, weight and an optional body fat %. Nothing is
/// saved until the guide is saved.
class AboutYouStep extends StatelessWidget {
  const AboutYouStep({
    super.key,
    required this.draft,
    this.bodyFatError,
    this.targetWeightError,
  });

  final GuideDraft draft;

  /// The API's message for an out-of-range body fat %.
  final String? bodyFatError;
  final String? targetWeightError;

  static const birthYearKey = Key('guide-birth-year');
  static const heightKey = Key('guide-height');
  static const weightKey = Key('guide-weight');
  static const bodyFatKey = Key('guide-body-fat');
  static Key sexKey(String? sex) => Key('guide-sex-${sex ?? 'none'}');
  static Key sexReferenceKey(String ref) => Key('guide-sex-reference-$ref');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    String? missing(String field, String label) =>
        draft.missing.contains(field) ? l10n.targetsNeedsBodyData(label) : null;
    final now = DateTime.now().year;
    final year = draft.birthYearValue;
    final yearBad =
        draft.birthYear.text.trim().isNotEmpty &&
        (year == null || year < birthYearMin || year > now);
    return ListenableBuilder(
      listenable: draft,
      builder: (context, _) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            key: birthYearKey,
            controller: draft.birthYear,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: l10n.membersFormBirthYear,
              errorText: yearBad
                  ? l10n.membersFormBirthYearInvalid('$now')
                  : missing('birth_year', l10n.membersFormBirthYear),
            ),
            onChanged: (_) => draft.notify(),
          ),
          const SizedBox(height: SnTokens.space3),
          Text(l10n.membersFormSex, style: theme.textTheme.titleSmall),
          Wrap(
            spacing: SnTokens.space2,
            children: [
              for (final s in [...sexOptions, null])
                ChoiceChip(
                  key: sexKey(s),
                  label: Text(
                    s == null
                        ? l10n.targetsPregnancyPreferNot
                        : sexLabel(l10n, s),
                  ),
                  selected: draft.sex == s,
                  onSelected: (_) {
                    draft.sex = s;
                    draft.notify();
                  },
                ),
            ],
          ),
          if (draft.sex == null || draft.sex == 'other') ...[
            const SizedBox(height: SnTokens.space3),
            Text(
              l10n.targetsSexReferenceTitle,
              style: theme.textTheme.titleSmall,
            ),
            if (draft.missing.contains('sex') && draft.sex == null)
              Text(
                l10n.targetsNeedsBodyData(l10n.membersFormSex),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            Wrap(
              spacing: SnTokens.space2,
              children: [
                for (final r in sexReferenceOptions)
                  ChoiceChip(
                    key: sexReferenceKey(r),
                    label: Text(switch (r) {
                      'female' => l10n.targetsSexReferenceFemale,
                      'male' => l10n.targetsSexReferenceMale,
                      _ => l10n.targetsSexReferenceAverage,
                    }),
                    selected: draft.sexReference == r,
                    onSelected: (_) {
                      draft.sexReference = r;
                      draft.notify();
                    },
                  ),
              ],
            ),
          ],
          const SizedBox(height: SnTokens.space3),
          TextField(
            key: heightKey,
            controller: draft.height,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: l10n.membersFormHeightCm,
              errorText: missing('height_cm', l10n.membersFormHeightCm),
            ),
            onChanged: (_) => draft.notify(),
          ),
          const SizedBox(height: SnTokens.space3),
          TextField(
            key: weightKey,
            controller: draft.weight,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: l10n.membersFormWeightKg,
              errorText: missing('weight_kg', l10n.membersFormWeightKg),
            ),
            onChanged: (_) => draft.notify(),
          ),
          const SizedBox(height: SnTokens.space3),
          TextField(
            key: bodyFatKey,
            controller: draft.bodyFat,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: l10n.targetsBodyFatLabel,
              helperText: l10n.targetsBodyFatHint,
              helperMaxLines: 4,
              errorText: bodyFatError,
              errorMaxLines: 3,
            ),
            onChanged: (_) => draft.notify(),
          ),
        ],
      ),
    );
  }
}
