// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_status.dart';
import 'nutri_score_grade.dart';
import 'nutrients_out.dart';

part 'compare_side.g.dart';

@JsonSerializable()
class CompareSide {
  const CompareSide({
    required this.attribution,
    required this.barcode,
    required this.brand,
    required this.grade,
    required this.highIn,
    required this.memberStatus,
    required this.name,
    required this.per100g,
    required this.productId,
  });

  factory CompareSide.fromJson(Map<String, Object?> json) =>
      _$CompareSideFromJson(json);

  final String? attribution;
  final String? barcode;
  final String? brand;
  final NutriScoreGrade? grade;
  @JsonKey(name: 'high_in')
  final List<String> highIn;

  /// The rules engine's verdict for member_id (only when member_id is given)
  @JsonKey(name: 'member_status')
  final MemberStatus? memberStatus;
  final String name;
  @JsonKey(name: 'per_100g')
  final NutrientsOut per100g;

  /// Our own product; null for Open Food Facts
  @JsonKey(name: 'product_id')
  final String? productId;

  Map<String, Object?> toJson() => _$CompareSideToJson(this);
}
