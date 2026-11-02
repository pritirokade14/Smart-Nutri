// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'product_out.dart';

part 'public_product_out.g.dart';

@JsonSerializable()
class PublicProductOut {
  const PublicProductOut({
    required this.product,
    required this.report,
    required this.scoreLabel,
  });

  factory PublicProductOut.fromJson(Map<String, Object?> json) =>
      _$PublicProductOutFromJson(json);

  final ProductOut product;
  final dynamic report;
  @JsonKey(name: 'score_label')
  final String scoreLabel;

  Map<String, Object?> toJson() => _$PublicProductOutToJson(this);
}
