// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'follow_ups.dart';
import 'user_types_in_types.dart';

part 'user_types_in.g.dart';

/// `types == []` is "Skip for now" (P9-R3). The order is the user's tap order.
@JsonSerializable()
class UserTypesIn {
  const UserTypesIn({required this.types, this.followUps});

  factory UserTypesIn.fromJson(Map<String, Object?> json) =>
      _$UserTypesInFromJson(json);

  @JsonKey(name: 'follow_ups')
  final FollowUps? followUps;
  final List<UserTypesInTypes> types;

  Map<String, Object?> toJson() => _$UserTypesInToJson(this);
}
