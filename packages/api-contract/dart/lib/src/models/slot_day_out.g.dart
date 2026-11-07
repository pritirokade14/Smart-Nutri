// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_day_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotDayOut _$SlotDayOutFromJson(Map<String, dynamic> json) => SlotDayOut(
  archived: json['archived'] as bool,
  customLabel: json['custom_label'] as String?,
  entries: (json['entries'] as List<dynamic>)
      .map((e) => MealOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  incomplete: IncompleteNutrients.fromJson(
    json['incomplete'] as Map<String, dynamic>,
  ),
  labelKey: json['label_key'] as String?,
  position: (json['position'] as num).toInt(),
  slotId: json['slot_id'] as String,
  totals: Totals.fromJson(json['totals'] as Map<String, dynamic>),
);

Map<String, dynamic> _$SlotDayOutToJson(SlotDayOut instance) =>
    <String, dynamic>{
      'archived': instance.archived,
      'custom_label': instance.customLabel,
      'entries': instance.entries,
      'incomplete': instance.incomplete,
      'label_key': instance.labelKey,
      'position': instance.position,
      'slot_id': instance.slotId,
      'totals': instance.totals,
    };
