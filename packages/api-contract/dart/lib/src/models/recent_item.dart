// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'nutri_score_grade.dart';
import 'recent_item_source_kind.dart';

part 'recent_item.g.dart';

@JsonSerializable()
class RecentItem {
  const RecentItem({
    required this.attribution,
    required this.barcode,
    required this.grade,
    required this.grams,
    required this.lastEatenAt,
    required this.mealSlotId,
    required this.name,
    required this.productId,
    required this.sourceKind,
    this.attributions,
    this.foodId,
    this.quantity,
    this.unit,
  });

  factory RecentItem.fromJson(Map<String, Object?> json) =>
      _$RecentItemFromJson(json);

  final String? attribution;
  final List<String>? attributions;
  final String? barcode;

  /// A generic food or dish; log it again with `food_id`
  @JsonKey(name: 'food_id')
  final String? foodId;
  final NutriScoreGrade? grade;
  final num grams;
  @JsonKey(name: 'last_eaten_at')
  final DateTime lastEatenAt;
  @JsonKey(name: 'meal_slot_id')
  final String mealSlotId;
  final String name;
  @JsonKey(name: 'product_id')
  final String? productId;

  /// The portion as last logged, with `unit`; null for older entries
  final num? quantity;
  @JsonKey(name: 'source_kind')
  final RecentItemSourceKind sourceKind;
  final String? unit;

  Map<String, Object?> toJson() => _$RecentItemToJson(this);
}
