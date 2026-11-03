// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'upload_url_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UploadUrlIn _$UploadUrlInFromJson(Map<String, dynamic> json) =>
    UploadUrlIn(ext: UploadUrlInExt.fromJson(json['ext'] as String));

Map<String, dynamic> _$UploadUrlInToJson(UploadUrlIn instance) =>
    <String, dynamic>{'ext': _$UploadUrlInExtEnumMap[instance.ext]!};

const _$UploadUrlInExtEnumMap = {
  UploadUrlInExt.jpg: 'jpg',
  UploadUrlInExt.png: 'png',
  UploadUrlInExt.webp: 'webp',
  UploadUrlInExt.$unknown: r'$unknown',
};
