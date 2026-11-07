// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'weights_deleted_out.g.dart';

@JsonSerializable()
class WeightsDeletedOut {
  const WeightsDeletedOut({required this.deleted});

  factory WeightsDeletedOut.fromJson(Map<String, Object?> json) =>
      _$WeightsDeletedOutFromJson(json);

  final int deleted;

  Map<String, Object?> toJson() => _$WeightsDeletedOutToJson(this);
}
