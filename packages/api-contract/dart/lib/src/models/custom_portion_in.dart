// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'custom_portion_in_unit.dart';

part 'custom_portion_in.g.dart';

@JsonSerializable()
class CustomPortionIn {
  const CustomPortionIn({required this.gramsPerUnit, required this.unit});

  factory CustomPortionIn.fromJson(Map<String, Object?> json) =>
      _$CustomPortionInFromJson(json);

  /// The amount of one unit in the food's basis
  @JsonKey(name: 'grams_per_unit')
  final num gramsPerUnit;

  /// A count or volume unit (never g or serving)
  final CustomPortionInUnit unit;

  Map<String, Object?> toJson() => _$CustomPortionInToJson(this);
}
