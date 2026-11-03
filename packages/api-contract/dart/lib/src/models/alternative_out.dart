// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_status.dart';
import 'nutri_score_grade.dart';

part 'alternative_out.g.dart';

/// A product in the same Open Food Facts category with a strictly better Nutri-Score.
/// (calculated by SmartNutri). Open it with ``products_get_by_barcode``.
@JsonSerializable()
class AlternativeOut {
  const AlternativeOut({
    required this.attribution,
    required this.barcode,
    required this.brand,
    required this.grade,
    required this.highIn,
    required this.imageUrl,
    required this.memberStatus,
    required this.name,
    required this.productId,
    required this.sugarsG,
  });

  factory AlternativeOut.fromJson(Map<String, Object?> json) =>
      _$AlternativeOutFromJson(json);

  /// "attribution.off": credit Open Food Facts
  final String? attribution;
  final String? barcode;
  final String? brand;
  final NutriScoreGrade grade;
  @JsonKey(name: 'high_in')
  final List<String> highIn;
  @JsonKey(name: 'image_url')
  final String? imageUrl;

  /// The rules engine's verdict for member_id (only when member_id is given)
  @JsonKey(name: 'member_status')
  final MemberStatus? memberStatus;
  final String name;
  @JsonKey(name: 'product_id')
  final String? productId;

  /// Per 100 g/ml; null if not on the label
  @JsonKey(name: 'sugars_g')
  final num? sugarsG;

  Map<String, Object?> toJson() => _$AlternativeOutToJson(this);
}
