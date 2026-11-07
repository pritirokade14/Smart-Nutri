// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'copy_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CopyIn _$CopyInFromJson(Map<String, dynamic> json) => CopyIn(
  clientId: json['client_id'] as String,
  fromDate: DateTime.parse(json['from_date'] as String),
  toDate: DateTime.parse(json['to_date'] as String),
  fromSlotId: json['from_slot_id'] as String?,
  memberId: json['member_id'] as String?,
  toSlotId: json['to_slot_id'] as String?,
);

Map<String, dynamic> _$CopyInToJson(CopyIn instance) => <String, dynamic>{
  'client_id': instance.clientId,
  'from_date': instance.fromDate.toIso8601String(),
  'from_slot_id': instance.fromSlotId,
  'member_id': instance.memberId,
  'to_date': instance.toDate.toIso8601String(),
  'to_slot_id': instance.toSlotId,
};
