import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// "Information, not medical advice." On every verdict view and on the
/// screens that lead to one.
class DisclaimerFooter extends StatelessWidget {
  const DisclaimerFooter({super.key, this.text});

  /// Overrides the common disclaimer with an equivalent i18n string (e.g.
  /// `confirm.not_medical_advice`).
  final String? text;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final style = Theme.of(
      context,
    ).textTheme.bodySmall?.copyWith(color: c.textSecondary);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space1 / 2),
            child: Icon(
              Icons.info_outline_rounded,
              size: SnTokens.fontSizeMd,
              color: c.textSecondary,
            ),
          ),
          const SizedBox(width: SnTokens.space2),
          Flexible(
            child: Text(
              text ?? l10n.commonDisclaimer,
              style: style,
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }
}
