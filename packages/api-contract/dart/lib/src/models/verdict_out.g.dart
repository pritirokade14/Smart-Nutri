// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'verdict_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VerdictOut _$VerdictOutFromJson(Map<String, dynamic> json) => VerdictOut(
  memberId: json['member_id'] as String,
  memberName: json['member_name'] as String,
  profileSetUp: json['profile_set_up'] as bool,
  reasons: (json['reasons'] as List<dynamic>)
      .map((e) => ReasonOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  status: VerdictOutStatus.fromJson(json['status'] as String),
);

Map<String, dynamic> _$VerdictOutToJson(VerdictOut instance) =>
    <String, dynamic>{
      'member_id': instance.memberId,
      'member_name': instance.memberName,
      'profile_set_up': instance.profileSetUp,
      'reasons': instance.reasons,
      'status': _$VerdictOutStatusEnumMap[instance.status]!,
    };

const _$VerdictOutStatusEnumMap = {
  VerdictOutStatus.ok: 'ok',
  VerdictOutStatus.caution: 'caution',
  VerdictOutStatus.unknown: 'unknown',
  VerdictOutStatus.avoid: 'avoid',
  VerdictOutStatus.$unknown: r'$unknown',
};
