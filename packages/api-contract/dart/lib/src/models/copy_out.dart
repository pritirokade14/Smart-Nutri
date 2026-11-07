// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_out.dart';

part 'copy_out.g.dart';

@JsonSerializable()
class CopyOut {
  const CopyOut({required this.created});

  factory CopyOut.fromJson(Map<String, Object?> json) =>
      _$CopyOutFromJson(json);

  /// The copies, in the order of their sources
  final List<MealOut> created;

  Map<String, Object?> toJson() => _$CopyOutToJson(this);
}
