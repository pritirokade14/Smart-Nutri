// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'prefill_change.dart';
import 'prefill_suggestion_goal_choice.dart';

part 'prefill_suggestion.g.dart';

/// Suggestions for the account holder's own member, recomputed from the member on every.
/// read, so it is empty once the user has confirmed (Task 2, P9-R9).
@JsonSerializable()
class PrefillSuggestion {
  const PrefillSuggestion({
    required this.changes,
    required this.goalChoice,
    required this.memberId,
    required this.needsHealthConsent,
  });

  factory PrefillSuggestion.fromJson(Map<String, Object?> json) =>
      _$PrefillSuggestionFromJson(json);

  /// [] means nothing to confirm: the client skips the review screen
  final List<PrefillChange> changes;

  /// Goal conflict (weight loss and gym 'build muscle'): no goal change is in `changes`; the user picks one of these or neither
  @JsonKey(name: 'goal_choice')
  final List<PrefillSuggestionGoalChoice>? goalChoice;

  /// Always the primary member (relation self)
  @JsonKey(name: 'member_id')
  final String memberId;

  /// A change touches a health field and `health_data` is not active
  @JsonKey(name: 'needs_health_consent')
  final bool needsHealthConsent;

  Map<String, Object?> toJson() => _$PrefillSuggestionToJson(this);
}
