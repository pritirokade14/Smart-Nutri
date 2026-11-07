// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'recent_item.dart';

part 'recents_out.g.dart';

@JsonSerializable()
class RecentsOut {
  const RecentsOut({required this.items});

  factory RecentsOut.fromJson(Map<String, Object?> json) =>
      _$RecentsOutFromJson(json);

  final List<RecentItem> items;

  Map<String, Object?> toJson() => _$RecentsOutToJson(this);
}
