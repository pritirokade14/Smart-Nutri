import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../core/theme/verdict_colors.dart';
import '../../../shared/widgets/verdict_badge.dart';
import '../domain/reasons.dart';
import 'reason_line.dart';

/// The engine status to display. A status this build does not recognise is
/// shown as `unknown` (grey, "Label unclear"), never as `ok`.
String displayStatus(VerdictOutStatus status) =>
    status == VerdictOutStatus.$unknown ? 'unknown' : status.json!;

String localizedStatus(AppLocalizations l10n, String status) =>
    verdictStatusLabel(l10n, status);

/// The card's headline: "`status` for you" for the account holder, otherwise
/// "`status` for `name`". Display only; the status is the API's.
String verdictHeadline(AppLocalizations l10n, VerdictOut verdict) {
  final label = localizedStatus(l10n, displayStatus(verdict.status));
  if (verdict.isPrimary) return l10n.verdictForYou(label);
  final name = verdict.memberName.isEmpty ? l10n.resultYou : verdict.memberName;
  return l10n.verdictForMember(name, label);
}

/// One member's verdict, exactly as the API returned it: a "`status` for
/// `name`" headline, colour from the verdict tokens, and reasons in API
/// order. The engine's top reason (`reasons[0]`) is always shown first; of
/// the rest, avoid, unknown and allergen reasons are always visible and the
/// others sit behind a toggle (R22).
class VerdictCard extends StatefulWidget {
  const VerdictCard({super.key, required this.verdict, this.action});

  final VerdictOut verdict;

  /// An optional action under the reasons (e.g. "I ate this"). It never
  /// changes what the card shows.
  final Widget? action;

  static const statusBadgeKey = Key('verdict-status-badge');
  static const reasonsToggleKey = Key('verdict-reasons-toggle');
  static const reasonsToggleSemanticsKey = Key('verdict-reasons-toggle-sem');
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
    final headline = verdictHeadline(l10n, verdict);
    final groups = topFirstReasons(displayReasons(verdict.reasons));

    final c = SnColors.of(context);
    final tone = verdictTone(c, status);
    const radius = Radius.circular(SnTokens.radiusLg);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: SnTokens.space2),
      decoration: BoxDecoration(
        color: c.surface,
        borderRadius: const BorderRadius.all(radius),
        border: Border.all(color: tone.color, width: 1.5),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header: tinted with the verdict, with the member and the badge.
          Container(
            color: tone.surface,
            padding: const EdgeInsets.symmetric(
              horizontal: SnTokens.space4,
              vertical: SnTokens.space3,
            ),
            child: Row(
              children: [
                Container(
                  width: SnTokens.space6 + SnTokens.space2,
                  height: SnTokens.space6 + SnTokens.space2,
                  decoration: BoxDecoration(
                    color: c.surface,
                    shape: BoxShape.circle,
                    border: Border.all(color: tone.color, width: 1.5),
                  ),
                  child: Icon(
                    Icons.person_rounded,
                    color: tone.color,
                    size: SnTokens.fontSizeXl,
                  ),
                ),
                const SizedBox(width: SnTokens.space3),
                Expanded(
                  child: Text(
                    headline,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontSize: SnTokens.fontSizeLg,
                    ),
                  ),
                ),
                const SizedBox(width: SnTokens.space2),
                VerdictBadge(
                  status: status,
                  surfaceKey: VerdictCard.statusBadgeKey,
                  large: true,
                ),
              ],
            ),
          ),
          // Body only when there is something to show (no empty band).
          if (!verdict.profileSetUp ||
              groups.visible.isNotEmpty ||
              groups.collapsed.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(
                SnTokens.space4,
                SnTokens.space3,
                SnTokens.space4,
                SnTokens.space3,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (!verdict.profileSetUp)
                    Padding(
                      padding: const EdgeInsets.only(bottom: SnTokens.space2),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.person_outline_rounded,
                            size: SnTokens.fontSizeMd,
                            color: c.textSecondary,
                          ),
                          const SizedBox(width: SnTokens.space2),
                          Expanded(
                            child: Text(
                              l10n.verdictProfileNotSetUp,
                              key: VerdictCard.profileNoteKey,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: c.textSecondary,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  for (final r in groups.visible) ReasonLine(reason: r),
                  if (groups.collapsed.isNotEmpty) ...[
                    if (_expanded)
                      for (final r in groups.collapsed) ReasonLine(reason: r),
                    Align(
                      alignment: AlignmentDirectional.centerStart,
                      child: Semantics(
                        key: VerdictCard.reasonsToggleSemanticsKey,
                        expanded: _expanded,
                        button: true,
                        child: TextButton.icon(
                          key: VerdictCard.reasonsToggleKey,
                          style: TextButton.styleFrom(
                            padding: EdgeInsets.zero,
                            minimumSize: const Size(0, SnTokens.space7),
                          ),
                          onPressed: () =>
                              setState(() => _expanded = !_expanded),
                          icon: Icon(
                            _expanded
                                ? Icons.expand_less_rounded
                                : Icons.expand_more_rounded,
                          ),
                          label: Text(
                            _expanded
                                ? l10n.verdictHideReasons
                                : l10n.verdictShowAllReasons,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          if (widget.action case final action?)
            Padding(
              padding: const EdgeInsets.fromLTRB(
                SnTokens.space4,
                SnTokens.space2,
                SnTokens.space4,
                SnTokens.space3,
              ),
              child: action,
            ),
        ],
      ),
    );
  }
}
