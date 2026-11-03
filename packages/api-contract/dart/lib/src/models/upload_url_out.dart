// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'upload_url_out.g.dart';

@JsonSerializable()
class UploadUrlOut {
  const UploadUrlOut({
    required this.expiresIn,
    required this.path,
    required this.uploadUrl,
  });

  factory UploadUrlOut.fromJson(Map<String, Object?> json) =>
      _$UploadUrlOutFromJson(json);

  @JsonKey(name: 'expires_in')
  final int expiresIn;
  final String path;
  @JsonKey(name: 'upload_url')
  final String uploadUrl;

  Map<String, Object?> toJson() => _$UploadUrlOutToJson(this);
}
