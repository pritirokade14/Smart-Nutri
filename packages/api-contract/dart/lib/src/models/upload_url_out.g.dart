// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'upload_url_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UploadUrlOut _$UploadUrlOutFromJson(Map<String, dynamic> json) => UploadUrlOut(
  expiresIn: (json['expires_in'] as num).toInt(),
  path: json['path'] as String,
  uploadUrl: json['upload_url'] as String,
);

Map<String, dynamic> _$UploadUrlOutToJson(UploadUrlOut instance) =>
    <String, dynamic>{
      'expires_in': instance.expiresIn,
      'path': instance.path,
      'upload_url': instance.uploadUrl,
    };
