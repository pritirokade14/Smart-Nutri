// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'weight_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeightIn _$WeightInFromJson(Map<String, dynamic> json) => WeightIn(
  weightKg: json['weight_kg'] as num,
  confirmUnusual: json['confirm_unusual'] as bool? ?? false,
  clientId: json['client_id'] as String?,
  memberId: json['member_id'] as String?,
);

Map<String, dynamic> _$WeightInToJson(WeightIn instance) => <String, dynamic>{
  'client_id': instance.clientId,
  'confirm_unusual': instance.confirmUnusual,
  'member_id': instance.memberId,
  'weight_kg': instance.weightKg,
};
