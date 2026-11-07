import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import 'guide_draft.dart';

String numbersDisplayLabel(AppLocalizations l10n, String value) =>
    switch (value) {
      'hide_energy' => l10n.settingsDiaryNumbersHideEnergy,
      'hide_all' => l10n.settingsDiaryNumbersHideAll,
      _ => l10n.settingsDiaryNumbersShow,
    };

/// How to see numbers: show (preselected), hide calories, hide all.
class NumbersChoice extends StatelessWidget {
  const NumbersChoice({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final String value;
  final ValueChanged<String> onChanged;

  static Key optionKey(String value) => Key('numbers-choice-$value');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          l10n.settingsDiaryNumbersTitle,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        RadioGroup<String>(
          groupValue: value,
          onChanged: (v) {
            if (v != null) onChanged(v);
          },
          child: Column(
            children: [
              for (final option in numbersDisplayOptions)
                RadioListTile<String>(
                  key: optionKey(option),
                  contentPadding: EdgeInsets.zero,
                  value: option,
                  title: Text(numbersDisplayLabel(l10n, option)),
                ),
            ],
          ),
        ),
        if (value != 'show')
          Text(
            l10n.settingsDiaryNumbersHideNote,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        const SizedBox(height: SnTokens.space2),
      ],
    );
  }
}
