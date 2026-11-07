// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'food_hit_group.dart';
import 'food_hit_kind.dart';
import 'nutri_score_grade.dart';

part 'food_hit.g.dart';

@JsonSerializable()
class FoodHit {
  const FoodHit({
    required this.attribution,
    required this.attributions,
    required this.brand,
    required this.grade,
    required this.group,
    required this.id,
    required this.isDish,
    required this.kind,
    required this.name,
  });

  factory FoodHit.fromJson(Map<String, Object?> json) =>
      _$FoodHitFromJson(json);

  /// "attribution.usda_fdc", "attribution.smartnutri_recipe" or "attribution.off"
  final String? attribution;

  /// Every credit this hit needs, in order
  final List<String> attributions;
  final String? brand;

  /// Nutri-Score calculated by SmartNutri; packaged products only, else null
  final NutriScoreGrade? grade;
  final FoodHitGroup group;

  /// A uuid, or the barcode for kind=off
  final String id;

  /// A documented Indian dish (calculated from ingredients)
  @JsonKey(name: 'is_dish')
  final bool isDish;
  final FoodHitKind kind;
  final String name;

  Map<String, Object?> toJson() => _$FoodHitToJson(this);
}
