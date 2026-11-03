// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'reason_out.dart';
import 'verdict_out_relation.dart';
import 'verdict_out_status.dart';

part 'verdict_out.g.dart';

@JsonSerializable()
class VerdictOut {
  const VerdictOut({
    required this.isPrimary,
    required this.memberId,
    required this.memberName,
    required this.profileSetUp,
    required this.reasons,
    required this.relation,
    required this.status,
  });

  factory VerdictOut.fromJson(Map<String, Object?> json) =>
      _$VerdictOutFromJson(json);

  /// The account holder: clients say 'for you'. Display only; never affects status.
  @JsonKey(name: 'is_primary')
  final bool isPrimary;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'member_name')
  final String memberName;

  /// False: age/allergies/diet may not be set; clients show a 'profile not set up' note. Display metadata only; never changes status or reasons.
  @JsonKey(name: 'profile_set_up')
  final bool profileSetUp;
  final List<ReasonOut> reasons;

  /// Display only (headline wording); never affects status.
  final VerdictOutRelation relation;
  final VerdictOutStatus status;

  Map<String, Object?> toJson() => _$VerdictOutToJson(this);
}
