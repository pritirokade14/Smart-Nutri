// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'prefill_change_field.dart';
import 'prefill_change_reason.dart';

part 'prefill_change.g.dart';

/// One suggested change to the primary member. Never applied by the API: the client sends.
/// `value` in `PATCH /v1/members/{member_id}` only if the user confirms it.
@JsonSerializable()
class PrefillChange {
  const PrefillChange({
    required this.added,
    required this.current,
    required this.field,
    required this.reason,
    required this.value,
  });

  factory PrefillChange.fromJson(Map<String, Object?> json) =>
      _$PrefillChangeFromJson(json);

  /// List fields: what is new (display); [] for diet/goal
  final List<String> added;

  /// The primary member's value now
  final dynamic current;
  final PrefillChangeField field;

  /// Which type suggested it (display only)
  final PrefillChangeReason reason;

  /// The FULL new value to send in MemberPatch if confirmed (never a removal)
  final dynamic value;

  Map<String, Object?> toJson() => _$PrefillChangeToJson(this);
}
