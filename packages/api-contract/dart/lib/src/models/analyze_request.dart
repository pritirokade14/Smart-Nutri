// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'analyze_request_language.dart';

part 'analyze_request.g.dart';

/// Exactly one product reference: our own ``product_id``, or a ``barcode`` (OFF products.
/// have no product_id). With no ``member_ids`` the account's primary member is used.
@JsonSerializable()
class AnalyzeRequest {
  const AnalyzeRequest({
    this.language = AnalyzeRequestLanguage.en,
    this.barcode,
    this.memberIds,
    this.productId,
  });

  factory AnalyzeRequest.fromJson(Map<String, Object?> json) =>
      _$AnalyzeRequestFromJson(json);

  final String? barcode;
  final AnalyzeRequestLanguage language;
  @JsonKey(name: 'member_ids')
  final List<String>? memberIds;
  @JsonKey(name: 'product_id')
  final String? productId;

  Map<String, Object?> toJson() => _$AnalyzeRequestToJson(this);
}
