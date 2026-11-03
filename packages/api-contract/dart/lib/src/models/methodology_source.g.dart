// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'methodology_source.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MethodologySource _$MethodologySourceFromJson(Map<String, dynamic> json) =>
    MethodologySource(
      id: json['id'] as String,
      title: json['title'] as String,
      url: json['url'] as String?,
      urlVerified: json['url_verified'] as bool,
    );

Map<String, dynamic> _$MethodologySourceToJson(MethodologySource instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'url': instance.url,
      'url_verified': instance.urlVerified,
    };
