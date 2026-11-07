// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'numbers_hidden.g.dart';

/// Which groups of numbers the user hid (also on the meals summary, Plan 10 Task 5).
@JsonSerializable()
class NumbersHidden {
  const NumbersHidden({required this.energy, required this.macros});

  factory NumbersHidden.fromJson(Map<String, Object?> json) =>
      _$NumbersHiddenFromJson(json);

  final bool energy;
  final bool macros;

  Map<String, Object?> toJson() => _$NumbersHiddenToJson(this);
}
