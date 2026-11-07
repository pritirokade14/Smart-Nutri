// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'body_data_in_sex.dart';

part 'body_data_in.g.dart';

/// Unsaved body data for a preview. A field that is SENT (even as null) overrides the.
/// stored one; a field left out keeps the stored value.
@JsonSerializable()
class BodyDataIn {
  const BodyDataIn({
    this.birthYear,
    this.bodyFatPct,
    this.heightCm,
    this.sex,
    this.weightKg,
  });

  factory BodyDataIn.fromJson(Map<String, Object?> json) =>
      _$BodyDataInFromJson(json);

  @JsonKey(name: 'birth_year')
  final int? birthYear;
  @JsonKey(name: 'body_fat_pct')
  final num? bodyFatPct;
  @JsonKey(name: 'height_cm')
  final num? heightCm;
  final BodyDataInSex? sex;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$BodyDataInToJson(this);
}
