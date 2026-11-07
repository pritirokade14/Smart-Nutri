// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diary_day_status_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiaryDayStatusIn _$DiaryDayStatusInFromJson(Map<String, dynamic> json) =>
    DiaryDayStatusIn(
      partialLogged: json['partial_logged'] as bool,
      memberId: json['member_id'] as String?,
    );

Map<String, dynamic> _$DiaryDayStatusInToJson(DiaryDayStatusIn instance) =>
    <String, dynamic>{
      'member_id': instance.memberId,
      'partial_logged': instance.partialLogged,
    };
