// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_slot_out.dart';

part 'meal_slots_list_out.g.dart';

@JsonSerializable()
class MealSlotsListOut {
  const MealSlotsListOut({required this.items});

  factory MealSlotsListOut.fromJson(Map<String, Object?> json) =>
      _$MealSlotsListOutFromJson(json);

  final List<MealSlotOut> items;

  Map<String, Object?> toJson() => _$MealSlotsListOutToJson(this);
}
