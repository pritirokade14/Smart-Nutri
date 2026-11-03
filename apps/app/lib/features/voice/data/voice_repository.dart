import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A failed voice question; [code] is the API `error.code`
/// (`rate_limited_voice`, `audio_too_long`, ...), `network`, or null.
class VoiceFailure implements Exception {
  const VoiceFailure(this.code);

  final String? code;

  @override
  String toString() => 'VoiceFailure($code)';
}

/// Asks one spoken question about one product for one member (F10).
abstract interface class VoiceRepository {
  /// Exactly one of [productId] and [barcode].
  Future<VoiceAnswer> ask({
    required File audio,
    required String memberId,
    required String language,
    String? productId,
    String? barcode,
  });
}

/// `POST /v1/voice/ask` through the generated client. The answer's verdict
/// comes only from the rules engine; it is shown and played unchanged.
class ApiVoiceRepository implements VoiceRepository {
  ApiVoiceRepository(this._client);

  final VoiceClient _client;

  @override
  Future<VoiceAnswer> ask({
    required File audio,
    required String memberId,
    required String language,
    String? productId,
    String? barcode,
  }) async {
    final lang = VoiceLanguage.fromJson(language);
    try {
      return await _client.voiceAsk(
        audio: audio,
        memberId: memberId,
        language: lang == VoiceLanguage.$unknown ? VoiceLanguage.en : lang,
        productId: productId,
        barcode: productId == null ? barcode : null,
      );
    } on Object catch (e) {
      throw VoiceFailure(apiErrorCode(e));
    }
  }
}

final voiceRepositoryProvider = Provider<VoiceRepository>(
  (ref) => ApiVoiceRepository(ref.watch(apiClientProvider).voice),
);
