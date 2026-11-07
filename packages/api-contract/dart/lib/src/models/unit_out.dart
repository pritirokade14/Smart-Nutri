// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'unit_out_kind.dart';

part 'unit_out.g.dart';

@JsonSerializable()
class UnitOut {
  const UnitOut({
    required this.code,
    required this.grams,
    required this.kind,
    required this.ml,
  });

  factory UnitOut.fromJson(Map<String, Object?> json) =>
      _$UnitOutFromJson(json);

  final String code;
  final num? grams;
  final UnitOutKind kind;
  final num? ml;

  Map<String, Object?> toJson() => _$UnitOutToJson(this);
}
