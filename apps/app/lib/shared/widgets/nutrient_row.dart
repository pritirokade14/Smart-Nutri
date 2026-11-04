import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// One line of a nutrition table: the label (with its unit) and the value as
/// given. A missing value says "Not on the label"; it is never shown as 0.
class NutrientRow extends StatelessWidget {
  const NutrientRow({
    super.key,
    required this.label,
    required this.value,
    this.divider = true,
  });

  final String label;

  /// The formatted value, or null when the label does not give one.
  final String? value;

  /// Draw a hairline under the row.
  final bool divider;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final value = this.value;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space2),
      decoration: divider
          ? BoxDecoration(
              border: Border(bottom: BorderSide(color: c.border)),
            )
          : null,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Text(label, style: theme.textTheme.bodyMedium)),
          const SizedBox(width: SnTokens.space3),
          if (value == null)
            Text(
              l10n.resultNotOnLabel,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
                fontStyle: FontStyle.italic,
              ),
            )
          else
            Text(
              value,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
        ],
      ),
    );
  }
}
