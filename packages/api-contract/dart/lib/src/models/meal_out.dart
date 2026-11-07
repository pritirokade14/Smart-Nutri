// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_out_basis.dart';
import 'meal_out_source_kind.dart';
import 'nutri_score_grade.dart';
import 'nutrient_snapshot.dart';
import 'portion_unit_out.dart';

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
    required this.incomplete,
    required this.localDate,
    required this.mealSlotId,
    required this.memberId,
    required this.nutrients,
    required this.productId,
    required this.productName,
    required this.sourceKind,
    required this.updatedAt,
    this.basis = MealOutBasis.g,
    this.attributions,
    this.foodId,
    this.portionUnits,
    this.quantity,
    this.unit,
  });

  factory MealOut.fromJson(Map<String, Object?> json) =>
      _$MealOutFromJson(json);

  /// "attribution.off" for Open Food Facts products (credit OFF), else null
  final String? attribution;

  /// Every credit this entry needs ("attribution.usda_fdc", "attribution.off", ...)
  final List<String>? attributions;

  /// Open Food Facts barcode; null for our products
  final String? barcode;

  /// Whether `grams` and the per-100 values are per g or per ml
  final MealOutBasis basis;
  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'eaten_at')
  final DateTime eatenAt;

  /// A generic food or Indian dish; null for other entries
  @JsonKey(name: 'food_id')
  final String? foodId;

  /// Nutri-Score calculated by SmartNutri at log time; null if not enough data
  final NutriScoreGrade? grade;

  /// The portion in grams; null for a quick add
  final num? grams;
  final String id;

  /// NutrientSnapshot keys that are unknown (null) on this entry, before hiding
  final List<String> incomplete;

  /// The day the entry belongs to, in the account's zone
  @JsonKey(name: 'local_date')
  final DateTime localDate;
  @JsonKey(name: 'meal_slot_id')
  final String mealSlotId;
  @JsonKey(name: 'member_id')
  final String memberId;
  final NutrientSnapshot nutrients;

  /// The units that resolved when the entry was logged (from its saved food), for the edit sheet. A PATCH may use only these
  @JsonKey(name: 'portion_units')
  final List<PortionUnitOut>? portionUnits;

  /// Our own product; null for Open Food Facts
  @JsonKey(name: 'product_id')
  final String? productId;

  /// The product name; the typed name (or empty) for a quick add
  @JsonKey(name: 'product_name')
  final String productName;

  /// The portion as typed (with unit); null for older entries
  final num? quantity;
  @JsonKey(name: 'source_kind')
  final MealOutSourceKind sourceKind;

  /// The household unit; null for older entries
  final String? unit;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$MealOutToJson(this);
}
