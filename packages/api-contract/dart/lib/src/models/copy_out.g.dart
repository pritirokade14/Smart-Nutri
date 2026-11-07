// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'copy_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CopyOut _$CopyOutFromJson(Map<String, dynamic> json) => CopyOut(
  created: (json['created'] as List<dynamic>)
      .map((e) => MealOut.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$CopyOutToJson(CopyOut instance) => <String, dynamic>{
  'created': instance.created,
};
