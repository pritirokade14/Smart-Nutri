// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'weight_point_out.g.dart';

@JsonSerializable()
class WeightPointOut {
  const WeightPointOut({
    required this.date,
    required this.outlier,
    required this.weightKg,
    required this.y,
  });

  factory WeightPointOut.fromJson(Map<String, Object?> json) =>
      _$WeightPointOutFromJson(json);

  final DateTime date;
  final bool outlier;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;
  final num? y;

  Map<String, Object?> toJson() => _$WeightPointOutToJson(this);
}
