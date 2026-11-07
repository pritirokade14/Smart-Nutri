// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'meal_slots_order_in.g.dart';

@JsonSerializable()
class MealSlotsOrderIn {
  const MealSlotsOrderIn({required this.ids, this.memberId});

  factory MealSlotsOrderIn.fromJson(Map<String, Object?> json) =>
      _$MealSlotsOrderInFromJson(json);

  final List<String> ids;
  @JsonKey(name: 'member_id')
  final String? memberId;

  Map<String, Object?> toJson() => _$MealSlotsOrderInToJson(this);
}
