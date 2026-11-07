// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'display_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DisplayOut _$DisplayOutFromJson(Map<String, dynamic> json) => DisplayOut(
  memberId: json['member_id'] as String,
  numbersDisplay: DisplayOutNumbersDisplay.fromJson(
    json['numbers_display'] as String,
  ),
  summaryView: DisplayOutSummaryView.fromJson(json['summary_view'] as String),
  updatedAt: DateTime.parse(json['updated_at'] as String),
);

Map<String, dynamic> _$DisplayOutToJson(DisplayOut instance) =>
    <String, dynamic>{
      'member_id': instance.memberId,
      'numbers_display':
          _$DisplayOutNumbersDisplayEnumMap[instance.numbersDisplay]!,
      'summary_view': _$DisplayOutSummaryViewEnumMap[instance.summaryView]!,
      'updated_at': instance.updatedAt.toIso8601String(),
    };

const _$DisplayOutNumbersDisplayEnumMap = {
  DisplayOutNumbersDisplay.valueShow: 'show',
  DisplayOutNumbersDisplay.hideEnergy: 'hide_energy',
  DisplayOutNumbersDisplay.hideAll: 'hide_all',
  DisplayOutNumbersDisplay.$unknown: r'$unknown',
};

const _$DisplayOutSummaryViewEnumMap = {
  DisplayOutSummaryView.remaining: 'remaining',
  DisplayOutSummaryView.consumed: 'consumed',
  DisplayOutSummaryView.$unknown: r'$unknown',
};
