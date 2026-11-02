import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../core/theme/verdict_colors.dart';
import '../domain/reasons.dart';
import 'reason_line.dart';

/// The engine status to display. A status this build does not recognise is
/// shown as `unknown` (grey, "Label unclear"), never as `ok`.
String displayStatus(VerdictOutStatus status) =>
    status == VerdictOutStatus.$unknown ? 'unknown' : status.json!;

String localizedStatus(AppLocalizations l10n, String status) =>
    switch (status) {
      'ok' => l10n.statusOk,
      'caution' => l10n.statusCaution,
      'avoid' => l10n.statusAvoid,
      _ => l10n.statusUnknown,
    };

/// One member's verdict, exactly as the API returned it: status, colour from
/// the verdict tokens, and reasons in API order.
class VerdictCard extends StatelessWidget {
  const VerdictCard({super.key, required this.verdict});

  final VerdictOut verdict;

  static const statusBadgeKey = Key('verdict-status-badge');

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final status = displayStatus(verdict.status);
    final color = verdictColor(status);
    final name = verdict.memberName.isEmpty
        ? l10n.resultYou
        : verdict.memberName;
    final reasons = displayReasons(verdict.reasons);
    final statusLabel = localizedStatus(l10n, status);

    final Widget? reasonsView = switch (reasons.length) {
      0 => null,
      1 => Text(reasonText(l10n, reasons.first)),
      // Top reason first; the rest (API order) behind the expand control.
      _ => ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: EdgeInsets.zero,
        shape: const Border(),
        collapsedShape: const Border(),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        title: Text(topReasonText(l10n, verdict)),
        children: [for (final r in reasons.skip(1)) ReasonLine(reason: r)],
      ),
    };

    return Card(
      margin: const EdgeInsets.symmetric(vertical: SnTokens.space2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
        side: BorderSide(color: color, width: 2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(name, style: theme.textTheme.titleMedium)),
                Container(
                  key: statusBadgeKey,
                  padding: const EdgeInsets.symmetric(
                    horizontal: SnTokens.space3,
                    vertical: SnTokens.space1,
                  ),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(SnTokens.radiusLg),
                  ),
                  child: Text(
                    statusLabel,
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: SnTokens.surfaceDefault,
                    ),
                  ),
                ),
              ],
            ),
            if (reasonsView != null) ...[
              const SizedBox(height: SnTokens.space2),
              reasonsView,
            ],
          ],
        ),
      ),
    );
  }
}
