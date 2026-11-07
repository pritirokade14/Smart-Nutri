// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'time_window.dart';

part 'meal_slot_create_in.g.dart';

@JsonSerializable()
class MealSlotCreateIn {
  const MealSlotCreateIn({
    required this.customLabel,
    this.clientId,
    this.defaultTimeWindow,
    this.memberId,
  });

  factory MealSlotCreateIn.fromJson(Map<String, Object?> json) =>
      _$MealSlotCreateInFromJson(json);

  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'custom_label')
  final String customLabel;
  @JsonKey(name: 'default_time_window')
  final TimeWindow? defaultTimeWindow;
  @JsonKey(name: 'member_id')
  final String? memberId;

  Map<String, Object?> toJson() => _$MealSlotCreateInToJson(this);
}
