// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'follow_ups.dart';
import 'prefill_suggestion.dart';
import 'user_types_out_active_type.dart';
import 'user_types_out_types.dart';

part 'user_types_out.g.dart';

@JsonSerializable()
class UserTypesOut {
  const UserTypesOut({
    required this.activeType,
    required this.answered,
    required this.answeredAt,
    required this.followUps,
    required this.prefill,
    required this.types,
  });

  factory UserTypesOut.fromJson(Map<String, Object?> json) =>
      _$UserTypesOutFromJson(json);

  /// Resolved: the stored value if still selected, else the highest-priority chosen type, else eat_better
  @JsonKey(name: 'active_type')
  final UserTypesOutActiveType activeType;

  /// False until the first PUT: clients show the picker
  final bool answered;
  @JsonKey(name: 'answered_at')
  final DateTime? answeredAt;
  @JsonKey(name: 'follow_ups')
  final FollowUps followUps;

  /// Suggested changes to the primary member (null until answered)
  final PrefillSuggestion? prefill;

  /// The user's tap order
  final List<UserTypesOutTypes> types;

  Map<String, Object?> toJson() => _$UserTypesOutToJson(this);
}
