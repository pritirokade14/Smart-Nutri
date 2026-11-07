// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_slot_out.dart';

part 'meal_slots_out.g.dart';

@JsonSerializable()
class MealSlotsOut {
  const MealSlotsOut({required this.items, required this.suggestedSlotId});

  factory MealSlotsOut.fromJson(Map<String, Object?> json) =>
      _$MealSlotsOutFromJson(json);

  final List<MealSlotOut> items;
  @JsonKey(name: 'suggested_slot_id')
  final String suggestedSlotId;

  Map<String, Object?> toJson() => _$MealSlotsOutToJson(this);
}
