// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'weights_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeightsOut _$WeightsOutFromJson(Map<String, dynamic> json) => WeightsOut(
  items: (json['items'] as List<dynamic>)
      .map((e) => WeightOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  numbersHidden: json['numbers_hidden'] as bool,
);

Map<String, dynamic> _$WeightsOutToJson(WeightsOut instance) =>
    <String, dynamic>{
      'items': instance.items,
      'numbers_hidden': instance.numbersHidden,
    };
