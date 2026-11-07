// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'custom_nutrients_in.dart';
import 'entered_out_values_per.dart';

part 'entered_out.g.dart';

@JsonSerializable()
class EnteredOut {
  const EnteredOut({
    required this.nutrients,
    required this.servingG,
    required this.valuesPer,
  });

  factory EnteredOut.fromJson(Map<String, Object?> json) =>
      _$EnteredOutFromJson(json);

  final CustomNutrientsIn nutrients;
  @JsonKey(name: 'serving_g')
  final num? servingG;
  @JsonKey(name: 'values_per')
  final EnteredOutValuesPer valuesPer;

  Map<String, Object?> toJson() => _$EnteredOutToJson(this);
}
