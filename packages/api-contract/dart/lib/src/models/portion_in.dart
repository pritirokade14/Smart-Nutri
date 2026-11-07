// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'portion_in.g.dart';

@JsonSerializable()
class PortionIn {
  const PortionIn({required this.gramsPerUnit});

  factory PortionIn.fromJson(Map<String, Object?> json) =>
      _$PortionInFromJson(json);

  /// The amount of one unit in the food's basis
  @JsonKey(name: 'grams_per_unit')
  final num gramsPerUnit;

  Map<String, Object?> toJson() => _$PortionInToJson(this);
}
