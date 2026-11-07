// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'custom_portion_out.g.dart';

@JsonSerializable()
class CustomPortionOut {
  const CustomPortionOut({required this.gramsPerUnit, required this.unit});

  factory CustomPortionOut.fromJson(Map<String, Object?> json) =>
      _$CustomPortionOutFromJson(json);

  @JsonKey(name: 'grams_per_unit')
  final num gramsPerUnit;
  final String unit;

  Map<String, Object?> toJson() => _$CustomPortionOutToJson(this);
}
