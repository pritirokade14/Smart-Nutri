// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'time_window.dart';

part 'meal_slot_out.g.dart';

@JsonSerializable()
class MealSlotOut {
  const MealSlotOut({
    required this.archived,
    required this.customLabel,
    required this.defaultTimeWindow,
    required this.id,
    required this.isDefault,
    required this.labelKey,
    required this.memberId,
    required this.position,
  });

  factory MealSlotOut.fromJson(Map<String, Object?> json) =>
      _$MealSlotOutFromJson(json);

  final bool archived;
  @JsonKey(name: 'custom_label')
  final String? customLabel;
  @JsonKey(name: 'default_time_window')
  final TimeWindow? defaultTimeWindow;
  final String id;
  @JsonKey(name: 'is_default')
  final bool isDefault;
  @JsonKey(name: 'label_key')
  final String? labelKey;
  @JsonKey(name: 'member_id')
  final String memberId;
  final int position;

  Map<String, Object?> toJson() => _$MealSlotOutToJson(this);
}
