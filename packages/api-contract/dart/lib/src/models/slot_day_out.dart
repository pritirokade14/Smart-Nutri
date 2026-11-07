// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'incomplete_nutrients.dart';
import 'meal_out.dart';
import 'totals.dart';

part 'slot_day_out.g.dart';

@JsonSerializable()
class SlotDayOut {
  const SlotDayOut({
    required this.archived,
    required this.customLabel,
    required this.entries,
    required this.incomplete,
    required this.labelKey,
    required this.position,
    required this.slotId,
    required this.totals,
  });

  factory SlotDayOut.fromJson(Map<String, Object?> json) =>
      _$SlotDayOutFromJson(json);

  final bool archived;

  /// User text: shown as typed, never translated
  @JsonKey(name: 'custom_label')
  final String? customLabel;
  final List<MealOut> entries;
  final IncompleteNutrients incomplete;

  /// i18n key of a default slot's name
  @JsonKey(name: 'label_key')
  final String? labelKey;
  final int position;
  @JsonKey(name: 'slot_id')
  final String slotId;
  final Totals totals;

  Map<String, Object?> toJson() => _$SlotDayOutToJson(this);
}
