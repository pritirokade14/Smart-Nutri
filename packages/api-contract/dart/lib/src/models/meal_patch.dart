// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_patch_unit.dart';
import 'quick_in.dart';

part 'meal_patch.g.dart';

/// Edit an entry. ``null`` means unchanged (Ruling E10: the generated Dart client sends.
/// every unset field as null). At least one field must be set. ``quick`` is for quick-add.
/// entries only; the portion fields are for the others.
@JsonSerializable()
class MealPatch {
  const MealPatch({
    this.eatenAt,
    this.grams,
    this.mealSlotId,
    this.quantity,
    this.quick,
    this.servings,
    this.unit,
  });

  factory MealPatch.fromJson(Map<String, Object?> json) =>
      _$MealPatchFromJson(json);

  @JsonKey(name: 'eaten_at')
  final DateTime? eatenAt;
  final num? grams;
  @JsonKey(name: 'meal_slot_id')
  final String? mealSlotId;

  /// With `unit`: a new portion in a household unit. Only units that resolved when the entry was logged (`portion_units`) are accepted, else 422 unit_grams_unknown
  final num? quantity;
  final QuickIn? quick;
  final num? servings;
  final MealPatchUnit? unit;

  Map<String, Object?> toJson() => _$MealPatchToJson(this);
}
