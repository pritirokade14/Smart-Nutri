// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

/// The longest question; recording stops and sends by itself at this point.
const voiceMaxDuration = Duration(seconds: 30);

/// Who and what a question is about. Exactly one of [productId] (our
/// catalogue) and [barcode] (Open Food Facts) is set.
class VoiceTarget {
  const VoiceTarget({
    required this.memberId,
    required this.language,
    this.productId,
    this.barcode,
  });

  /// The target for a result's product, or null when it has neither an id
  /// nor a barcode. Our own id wins over the barcode.
  static VoiceTarget? forProduct({
    required String memberId,
    required String? productId,
    required String? barcode,
    required String language,
  }) {
    if (productId != null && productId.isNotEmpty) {
      return VoiceTarget(
        memberId: memberId,
        productId: productId,
        language: language,
      );
    }
    if (barcode != null && barcode.isNotEmpty) {
      return VoiceTarget(
        memberId: memberId,
        barcode: barcode,
        language: language,
      );
    }
    return null;
  }

  final String memberId;
  final String? productId;
  final String? barcode;

  /// `en`, `hi` or `mr`: the answer's language.
  final String language;
}

sealed class VoiceState {
  const VoiceState();
}

class VoiceIdle extends VoiceState {
  const VoiceIdle();

  @override
  bool operator ==(Object other) => other is VoiceIdle;

  @override
  int get hashCode => 0;
}

class VoiceRecording extends VoiceState {
  const VoiceRecording(this.elapsed);

  final Duration elapsed;

  @override
  bool operator ==(Object other) =>
      other is VoiceRecording && other.elapsed == elapsed;

  @override
  int get hashCode => elapsed.hashCode;
}

class VoiceUploading extends VoiceState {
  const VoiceUploading();

  @override
  bool operator ==(Object other) => other is VoiceUploading;

  @override
  int get hashCode => 1;
}

/// The API's answer: the engine's verdict sentence first, then the
/// explanation, with its audio. Kept in memory only.
class VoicePlaying extends VoiceState {
  const VoicePlaying(this.answer);

  final VoiceAnswer answer;
}

/// [messageKey] is an i18n key (`voice.*`, `consent.required_to_continue`),
/// or `error` for an API [code] shown with `error.<code>`.
class VoiceError extends VoiceState {
  const VoiceError(this.messageKey, {this.code});

  final String messageKey;
  final String? code;
}

/// The message key for an API error code (Plan 7 Task 8).
String voiceErrorKey(String? code) => switch (code) {
  'rate_limited_voice' => 'voice.rate_limited',
  'audio_too_long' => 'voice.too_long',
  'voice_not_understood' => 'voice.not_understood',
  'ai_unavailable' => 'voice.ai_unavailable',
  // The consent screen is already open (ai_processing or terms).
  'consent_required' => 'consent.required_to_continue',
  _ => 'error',
};
