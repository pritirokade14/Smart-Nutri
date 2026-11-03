// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_status.dart';
import 'nutri_score_grade.dart';
import 'search_hit_source.dart';

part 'search_hit.g.dart';

/// Our own products first (``product_id``), then Open Food Facts (``barcode`` only: open.
/// with ``products_get_by_barcode``).
@JsonSerializable()
class SearchHit {
  const SearchHit({
    required this.attribution,
    required this.barcode,
    required this.brand,
    required this.grade,
    required this.memberStatus,
    required this.name,
    required this.productId,
    required this.proteinG,
    required this.proteinPer100kcal,
    required this.source,
    this.offDegraded = false,
  });

  factory SearchHit.fromJson(Map<String, Object?> json) =>
      _$SearchHitFromJson(json);

  /// "attribution.off" for Open Food Facts hits
  final String? attribution;
  final String? barcode;
  final String? brand;

  /// Nutri-Score calculated by SmartNutri; null if unknown
  final NutriScoreGrade? grade;

  /// The rules engine's verdict. sort=relevance: only when member_id is given. sort=protein: for member_id or else the primary member (avoid is never returned)
  @JsonKey(name: 'member_status')
  final MemberStatus? memberStatus;
  final String name;

  /// true when the Open Food Facts search budget was spent and only our own catalogue is returned; clients show a small 'more results later' note
  @JsonKey(name: 'off_degraded')
  final bool offDegraded;
  @JsonKey(name: 'product_id')
  final String? productId;

  /// Protein per 100 g/ml (report.protein.per_100g); null if not on the label
  @JsonKey(name: 'protein_g')
  final num? proteinG;

  /// report.protein.per_100kcal; null without protein or energy
  @JsonKey(name: 'protein_per_100kcal')
  final num? proteinPer100kcal;
  final SearchHitSource source;

  Map<String, Object?> toJson() => _$SearchHitToJson(this);
}
