// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'portion_unit_out.g.dart';

@JsonSerializable()
class PortionUnitOut {
  const PortionUnitOut({required this.code, required this.gramsPerUnit});

  factory PortionUnitOut.fromJson(Map<String, Object?> json) =>
      _$PortionUnitOutFromJson(json);

  final String code;

  /// The amount of ONE unit in the entry's basis, as it was when logged
  @JsonKey(name: 'grams_per_unit')
  final num gramsPerUnit;

  Map<String, Object?> toJson() => _$PortionUnitOutToJson(this);
}
