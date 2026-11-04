import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';
import '../../core/theme/verdict_colors.dart';

/// The short label for an engine status. Anything unrecognised reads as
/// "Label unclear", never "OK".
String verdictStatusLabel(AppLocalizations l10n, String status) =>
    switch (status) {
      'ok' => l10n.statusOk,
      'caution' => l10n.statusCaution,
      'avoid' => l10n.statusAvoid,
      _ => l10n.statusUnknown,
    };

/// A verdict status as a pill: colour from the verdict tokens, an icon and a
/// short label, so the status never depends on colour alone. Renders exactly
/// the status it is given; an unrecognised status is shown as `unknown`.
class VerdictBadge extends StatelessWidget {
  const VerdictBadge({
    super.key,
    required this.status,
    this.surfaceKey,
    this.large = false,
  });

  final String status;

  /// Key for the coloured surface (tests read its fill colour).
  final Key? surfaceKey;

  /// A bigger badge for headers.
  final bool large;

  static IconData iconFor(String status) => switch (status) {
    'ok' => Icons.check_circle_rounded,
    'caution' => Icons.warning_rounded,
    'avoid' => Icons.block_rounded,
    _ => Icons.help_rounded,
  };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final shown = safeVerdictStatus(status);
    final tone = verdictTone(SnColors.of(context), shown);
    final label = verdictStatusLabel(l10n, shown);
    final textStyle =
        (large
                ? Theme.of(context).textTheme.labelLarge
                : Theme.of(context).textTheme.labelMedium)
            ?.copyWith(color: tone.onColor, fontWeight: FontWeight.w700);
    return Semantics(
      label: label,
      excludeSemantics: true,
      child: Container(
        key: surfaceKey,
        padding: EdgeInsets.symmetric(
          horizontal: large ? SnTokens.space3 : SnTokens.space2,
          vertical: large ? SnTokens.space2 : SnTokens.space1,
        ),
        decoration: BoxDecoration(
          color: tone.color,
          borderRadius: BorderRadius.circular(SnTokens.radiusFull),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              iconFor(shown),
              size: large ? SnTokens.fontSizeLg : SnTokens.fontSizeMd,
              color: tone.onColor,
            ),
            const SizedBox(width: SnTokens.space1),
            Text(label, style: textStyle),
          ],
        ),
      ),
    );
  }
}
