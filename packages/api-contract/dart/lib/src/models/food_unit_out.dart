// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'food_unit_out_kind.dart';
import 'food_unit_out_source.dart';

part 'food_unit_out.g.dart';

@JsonSerializable()
class FoodUnitOut {
  const FoodUnitOut({
    required this.code,
    required this.gramsPerUnit,
    required this.kind,
    required this.ml,
    required this.source,
    required this.userOverride,
  });

  factory FoodUnitOut.fromJson(Map<String, Object?> json) =>
      _$FoodUnitOutFromJson(json);

  final String code;

  /// The amount of ONE unit in the food's basis (grams, or ml for an ml-basis food), unrounded. Only units that resolve are listed
  @JsonKey(name: 'grams_per_unit')
  final num gramsPerUnit;
  final FoodUnitOutKind kind;

  /// Volume of one unit; volume units only
  final num? ml;
  final FoodUnitOutSource source;

  /// true when the account set this value itself
  @JsonKey(name: 'user_override')
  final bool userOverride;

  Map<String, Object?> toJson() => _$FoodUnitOutToJson(this);
}
