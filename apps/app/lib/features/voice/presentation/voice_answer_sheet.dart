import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/verdict_badge.dart';

/// The spoken answer on screen: the engine's status as a badge (verdict
/// tokens; `unknown` is never green), the answer text exactly as the API sent
/// it (it starts with the engine's verdict sentence), and "Information, not
/// medical advice". The question is shown back (never stored); a rules-only
/// (`fallback`) answer carries the "AI explanation isn't available" note.
class VoiceAnswerSheet extends StatelessWidget {
  const VoiceAnswerSheet({
    super.key,
    required this.answer,
    required this.onReplay,
    this.onClose,
  });

  final VoiceAnswer answer;
  final VoidCallback onReplay;
  final VoidCallback? onClose;

  static const badgeSurfaceKey = Key('voice-answer-badge');

  /// The status to show; one this build does not know is `unknown`.
  static String statusOf(VoiceAnswerVerdictStatus status) =>
      status == VoiceAnswerVerdictStatus.$unknown || status.json == null
      ? 'unknown'
      : status.json!;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space5,
        SnTokens.space2,
        SnTokens.space5,
        SnTokens.space5,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          VerdictBadge(
            status: statusOf(answer.verdictStatus),
            surfaceKey: badgeSurfaceKey,
            large: true,
          ),
          const SizedBox(height: SnTokens.space3),
          // The transcript is shown back, never stored.
          Text(
            l10n.voiceYouAsked(answer.question),
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
          const SizedBox(height: SnTokens.space2),
          Text(answer.answer, style: theme.textTheme.bodyLarge),
          if (answer.source == VoiceAnswerSource.fallback) ...[
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.explanationSourceFallbackNote,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ],
          const SizedBox(height: SnTokens.space3),
          Row(
            children: [
              Icon(Icons.volume_up_rounded, color: c.textSecondary),
              const SizedBox(width: SnTokens.space2),
              Expanded(
                child: Text(
                  l10n.voicePlaying,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: c.textSecondary,
                  ),
                ),
              ),
              TextButton.icon(
                icon: const Icon(Icons.replay_rounded),
                label: Text(l10n.voiceReplay),
                onPressed: onReplay,
              ),
            ],
          ),
          const DisclaimerFooter(),
          if (onClose case final close?)
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: TextButton(
                onPressed: close,
                child: Text(l10n.commonClose),
              ),
            ),
        ],
      ),
    );
  }
}
