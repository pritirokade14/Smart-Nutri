// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'display_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DisplayIn _$DisplayInFromJson(Map<String, dynamic> json) => DisplayIn(
  memberId: json['member_id'] as String?,
  numbersDisplay: json['numbers_display'] == null
      ? null
      : DisplayInNumbersDisplay.fromJson(json['numbers_display'] as String),
  summaryView: json['summary_view'] == null
      ? null
      : DisplayInSummaryView.fromJson(json['summary_view'] as String),
);

Map<String, dynamic> _$DisplayInToJson(DisplayIn instance) => <String, dynamic>{
  'member_id': instance.memberId,
  'numbers_display': _$DisplayInNumbersDisplayEnumMap[instance.numbersDisplay],
  'summary_view': _$DisplayInSummaryViewEnumMap[instance.summaryView],
};

const _$DisplayInNumbersDisplayEnumMap = {
  DisplayInNumbersDisplay.valueShow: 'show',
  DisplayInNumbersDisplay.hideEnergy: 'hide_energy',
  DisplayInNumbersDisplay.hideAll: 'hide_all',
  DisplayInNumbersDisplay.$unknown: r'$unknown',
};

const _$DisplayInSummaryViewEnumMap = {
  DisplayInSummaryView.remaining: 'remaining',
  DisplayInSummaryView.consumed: 'consumed',
  DisplayInSummaryView.$unknown: r'$unknown',
};
