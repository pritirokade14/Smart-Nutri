// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'upload_url_in_ext.dart';

part 'upload_url_in.g.dart';

@JsonSerializable()
class UploadUrlIn {
  const UploadUrlIn({required this.ext});

  factory UploadUrlIn.fromJson(Map<String, Object?> json) =>
      _$UploadUrlInFromJson(json);

  final UploadUrlInExt ext;

  Map<String, Object?> toJson() => _$UploadUrlInToJson(this);
}
