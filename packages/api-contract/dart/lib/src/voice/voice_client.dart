// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/voice_answer.dart';
import '../models/voice_language.dart';

part 'voice_client.g.dart';

@RestApi()
abstract class VoiceClient {
  factory VoiceClient(Dio dio, {String? baseUrl}) = _VoiceClient;

  /// Voice Ask.
  ///
  /// Answer a spoken question about one product for one family member.
  ///
  /// Send exactly one of `product_id` (our catalogue) or `barcode` (Open Food Facts). Audio:.
  /// at most 30 s and 5 MB; m4a/AAC, WAV, WebM, Ogg or mp3, detected from the bytes. The.
  /// verdict comes only from the rules engine; `answer` starts with it. Needs the.
  /// `ai_processing` consent. Rate-limited per account per day (`rate_limited_voice`).
  @MultiPart()
  @POST('/v1/voice/ask')
  Future<VoiceAnswer> voiceAsk({
    @Part(name: 'audio') required File audio,
    @Part(name: 'language') required VoiceLanguage language,
    @Part(name: 'member_id') required String memberId,
    @Part(name: 'barcode') String? barcode,
    @Part(name: 'product_id') String? productId,
  });
}
