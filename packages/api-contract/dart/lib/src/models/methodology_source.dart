// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'methodology_source.g.dart';

@JsonSerializable()
class MethodologySource {
  const MethodologySource({
    required this.id,
    required this.title,
    required this.url,
    required this.urlVerified,
  });

  factory MethodologySource.fromJson(Map<String, Object?> json) =>
      _$MethodologySourceFromJson(json);

  final String id;

  /// Document title as published (a citation, not UI prose).
  final String title;
  final String? url;

  /// False until a person has checked the link. Clients must not present an unverified link as authoritative.
  @JsonKey(name: 'url_verified')
  final bool urlVerified;

  Map<String, Object?> toJson() => _$MethodologySourceToJson(this);
}
