// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'time_window.dart';

part 'meal_slot_rename_in.g.dart';

/// Partial update: null means unchanged (Ruling E10); use the clear flags to remove.
@JsonSerializable()
class MealSlotRenameIn {
  const MealSlotRenameIn({
    this.customLabel,
    this.defaultTimeWindow,
    this.clearCustomLabel = false,
    this.clearTimeWindow = false,
  });

  factory MealSlotRenameIn.fromJson(Map<String, Object?> json) =>
      _$MealSlotRenameInFromJson(json);

  @JsonKey(name: 'clear_custom_label')
  final bool clearCustomLabel;
  @JsonKey(name: 'clear_time_window')
  final bool clearTimeWindow;
  @JsonKey(name: 'custom_label')
  final String? customLabel;
  @JsonKey(name: 'default_time_window')
  final TimeWindow? defaultTimeWindow;

  Map<String, Object?> toJson() => _$MealSlotRenameInToJson(this);
}
