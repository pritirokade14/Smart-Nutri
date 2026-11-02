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
/// the verdict tokens, and reasons in API order. Avoid, unknown and allergen
/// reasons are always visible; the rest sit behind a toggle (R22).
class VerdictCard extends StatefulWidget {
  const VerdictCard({super.key, required this.verdict});

  final VerdictOut verdict;

  static const statusBadgeKey = Key('verdict-status-badge');
  static const reasonsToggleKey = Key('verdict-reasons-toggle');
  static const profileNoteKey = Key('verdict-profile-note');

  @override
  State<VerdictCard> createState() => _VerdictCardState();
}

class _VerdictCardState extends State<VerdictCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final verdict = widget.verdict;
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final status = displayStatus(verdict.status);
    final color = verdictColor(status);
    final name = verdict.memberName.isEmpty
        ? l10n.resultYou
        : verdict.memberName;
    final groups = splitReasons(displayReasons(verdict.reasons));
    final statusLabel = localizedStatus(l10n, status);

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
                  key: VerdictCard.statusBadgeKey,
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
            if (!verdict.profileSetUp) ...[
              const SizedBox(height: SnTokens.space2),
              Text(
                l10n.verdictProfileNotSetUp,
                key: VerdictCard.profileNoteKey,
                style: theme.textTheme.bodySmall,
              ),
            ],
            if (groups.visible.isNotEmpty || groups.collapsed.isNotEmpty)
              const SizedBox(height: SnTokens.space2),
            for (final r in groups.visible) ReasonLine(reason: r),
            if (groups.collapsed.isNotEmpty) ...[
              TextButton(
                key: VerdictCard.reasonsToggleKey,
                onPressed: () => setState(() => _expanded = !_expanded),
                child: Text(
                  _expanded
                      ? l10n.verdictHideReasons
                      : l10n.verdictShowAllReasons,
                ),
              ),
              if (_expanded)
                for (final r in groups.collapsed) ReasonLine(reason: r),
            ],
          ],
        ),
      ),
    );
  }
}
