// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'me_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MeOut _$MeOutFromJson(Map<String, dynamic> json) => MeOut(
  createdAt: DateTime.parse(json['created_at'] as String),
  displayName: json['display_name'] as String?,
  email: json['email'] as String?,
  id: json['id'] as String,
  language: MeOutLanguage.fromJson(json['language'] as String),
);

Map<String, dynamic> _$MeOutToJson(MeOut instance) => <String, dynamic>{
  'created_at': instance.createdAt.toIso8601String(),
  'display_name': instance.displayName,
  'email': instance.email,
  'id': instance.id,
  'language': _$MeOutLanguageEnumMap[instance.language]!,
};

const _$MeOutLanguageEnumMap = {
  MeOutLanguage.en: 'en',
  MeOutLanguage.hi: 'hi',
  MeOutLanguage.mr: 'mr',
  MeOutLanguage.$unknown: r'$unknown',
};
