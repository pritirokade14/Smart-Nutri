// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'compare_better.dart';
import 'compare_side.dart';

part 'compare_out.g.dart';

@JsonSerializable()
class CompareOut {
  const CompareOut({required this.a, required this.b, required this.better});

  factory CompareOut.fromJson(Map<String, Object?> json) =>
      _$CompareOutFromJson(json);

  final CompareSide a;
  final CompareSide b;
  final CompareBetter better;

  Map<String, Object?> toJson() => _$CompareOutToJson(this);
}
