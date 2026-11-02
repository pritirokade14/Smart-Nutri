// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'reason_out.dart';
import 'verdict_out_status.dart';

part 'verdict_out.g.dart';

@JsonSerializable()
class VerdictOut {
  const VerdictOut({
    required this.memberId,
    required this.memberName,
    required this.reasons,
    required this.status,
  });

  factory VerdictOut.fromJson(Map<String, Object?> json) =>
      _$VerdictOutFromJson(json);

  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'member_name')
  final String memberName;
  final List<ReasonOut> reasons;
  final VerdictOutStatus status;

  Map<String, Object?> toJson() => _$VerdictOutToJson(this);
}
