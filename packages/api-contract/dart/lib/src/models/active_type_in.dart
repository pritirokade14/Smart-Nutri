// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'active_type_in_active_type.dart';

part 'active_type_in.g.dart';

@JsonSerializable()
class ActiveTypeIn {
  const ActiveTypeIn({required this.activeType});

  factory ActiveTypeIn.fromJson(Map<String, Object?> json) =>
      _$ActiveTypeInFromJson(json);

  @JsonKey(name: 'active_type')
  final ActiveTypeInActiveType activeType;

  Map<String, Object?> toJson() => _$ActiveTypeInToJson(this);
}
