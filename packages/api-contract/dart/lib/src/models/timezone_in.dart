// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'timezone_in.g.dart';

@JsonSerializable()
class TimezoneIn {
  const TimezoneIn({required this.timezone});

  factory TimezoneIn.fromJson(Map<String, Object?> json) =>
      _$TimezoneInFromJson(json);

  final String timezone;

  Map<String, Object?> toJson() => _$TimezoneInToJson(this);
}
