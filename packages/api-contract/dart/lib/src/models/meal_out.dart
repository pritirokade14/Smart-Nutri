// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'nutri_score_grade.dart';
import 'nutrient_snapshot.dart';

part 'meal_out.g.dart';

@JsonSerializable()
class MealOut {
  const MealOut({
    required this.attribution,
    required this.barcode,
    required this.clientId,
    required this.eatenAt,
    required this.grade,
    required this.grams,
    required this.id,
    required this.memberId,
    required this.nutrients,
    required this.productId,
    required this.productName,
  });

  factory MealOut.fromJson(Map<String, Object?> json) =>
      _$MealOutFromJson(json);

  /// "attribution.off" for Open Food Facts products (credit OFF), else null
  final String? attribution;

  /// Open Food Facts barcode; null for our products
  final String? barcode;
  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'eaten_at')
  final DateTime eatenAt;

  /// Nutri-Score calculated by SmartNutri at log time; null if not enough data
  final NutriScoreGrade? grade;
  final num grams;
  final String id;
  @JsonKey(name: 'member_id')
  final String memberId;
  final NutrientSnapshot nutrients;

  /// Our own product; null for Open Food Facts
  @JsonKey(name: 'product_id')
  final String? productId;
  @JsonKey(name: 'product_name')
  final String productName;

  Map<String, Object?> toJson() => _$MealOutToJson(this);
}
