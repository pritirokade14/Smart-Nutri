import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/platform/app_settings.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/open_settings_button.dart';
import '../domain/voice_state.dart';
import 'voice_answer_sheet.dart';
import 'voice_controller.dart';

/// The text for a voice error.
String voiceErrorText(AppLocalizations l10n, VoiceError e) =>
    switch (e.messageKey) {
      'voice.mic_denied' => l10n.voiceMicDenied,
      'voice.rate_limited' => l10n.voiceRateLimited,
      'voice.too_long' => l10n.voiceTooLong,
      'voice.not_understood' => l10n.voiceNotUnderstood,
      'voice.ai_unavailable' => l10n.voiceAiUnavailable,
      'consent.required_to_continue' => l10n.consentRequiredToContinue,
      _ => localizedErrorCode(l10n, e.code),
    };

String _clock(Duration d) =>
    '${d.inMinutes}:${(d.inSeconds % 60).toString().padLeft(2, '0')}';

/// Press and hold to ask about this product for [target]'s member; release
/// to send, slide away to cancel. Shows the elapsed time while recording and
/// opens the answer when it arrives.
class PushToTalkButton extends ConsumerStatefulWidget {
  const PushToTalkButton({super.key, required this.target, this.memberName});

  final VoiceTarget target;

  /// Used only for the accessible label; never logged or sent anywhere.
  final String? memberName;

  /// How far the finger may move before the recording is cancelled.
  static const cancelDistance = 80.0;

  @override
  ConsumerState<PushToTalkButton> createState() => _PushToTalkButtonState();
}

class _PushToTalkButtonState extends ConsumerState<PushToTalkButton> {
  bool _cancelled = false;
  bool _micPermanentlyDenied = false;

  VoiceController get _controller =>
      ref.read(voiceControllerProvider(widget.target.memberId).notifier);

  Future<void> _showAnswer(VoicePlaying playing) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (sheetContext) => VoiceAnswerSheet(
        answer: playing.answer,
        onReplay: _controller.replay,
        onClose: () => Navigator.of(sheetContext).pop(),
      ),
    );
    if (mounted) await _controller.dismiss();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final provider = voiceControllerProvider(widget.target.memberId);
    ref.listen(provider, (previous, next) {
      if (next is VoicePlaying && previous is! VoicePlaying) _showAnswer(next);
      if (next case VoiceError(messageKey: 'voice.mic_denied')) {
        ref.read(appSettingsProvider).noteDenied(microphonePermission).then((
          permanent,
        ) {
          if (mounted) setState(() => _micPermanentlyDenied = permanent);
        });
      }
    });
    final state = ref.watch(provider);
    final recording = state is VoiceRecording;
    final busy = state is VoiceUploading;
    final label = switch (state) {
      VoiceRecording() => l10n.voiceRecording,
      VoiceUploading() => l10n.voiceThinking,
      _ => l10n.voiceButtonHold,
    };
    final name = widget.memberName?.trim() ?? '';
    final semanticsLabel =
        state is! VoiceRecording && state is! VoiceUploading && name.isNotEmpty
        ? l10n.voiceButtonHoldFor(name)
        : label;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          button: true,
          label: semanticsLabel,
          excludeSemantics: true,
          child: GestureDetector(
            onLongPressStart: busy
                ? null
                : (_) {
                    _cancelled = false;
                    _controller.start(widget.target);
                  },
            onLongPressMoveUpdate: (d) {
              if (!_cancelled &&
                  d.offsetFromOrigin.distance >
                      PushToTalkButton.cancelDistance) {
                _cancelled = true;
                _controller.cancel();
              }
            },
            onLongPressEnd: (_) {
              if (!_cancelled) _controller.stopAndSend();
            },
            onLongPressCancel: () {
              if (!_cancelled) _controller.cancel();
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(
                horizontal: SnTokens.space4,
                vertical: SnTokens.space3,
              ),
              decoration: BoxDecoration(
                color: recording ? c.brand : c.brandSoft,
                borderRadius: BorderRadius.circular(SnTokens.radiusFull),
                border: Border.all(color: c.brand),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (busy)
                    SizedBox.square(
                      dimension: SnTokens.space4,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: c.brandStrong,
                      ),
                    )
                  else
                    Icon(
                      recording ? Icons.mic_rounded : Icons.mic_none_rounded,
                      color: recording ? c.textInverse : c.brandStrong,
                    ),
                  const SizedBox(width: SnTokens.space2),
                  Flexible(
                    child: Text(
                      label,
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: recording ? c.textInverse : c.brandStrong,
                      ),
                    ),
                  ),
                  if (state case VoiceRecording(:final elapsed)) ...[
                    const SizedBox(width: SnTokens.space2),
                    Text(
                      _clock(elapsed),
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: c.textInverse,
                        fontFeatures: const [FontFeature.tabularFigures()],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
        if (state case final VoiceError error) ...[
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Text(
              voiceErrorText(l10n, error),
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
          if (error.messageKey == 'voice.mic_denied' && _micPermanentlyDenied)
            const Padding(
              padding: EdgeInsets.only(top: SnTokens.space2),
              child: OpenSettingsButton(),
            ),
        ],
      ],
    );
  }
}
