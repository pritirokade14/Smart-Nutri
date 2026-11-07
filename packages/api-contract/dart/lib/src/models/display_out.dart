// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'display_out_numbers_display.dart';
import 'display_out_summary_view.dart';

part 'display_out.g.dart';

/// What `PUT /display` returns: only the display fields. It needs only `terms`, so it must.
/// never carry the pregnancy answer, the target weight or the direction.
@JsonSerializable()
class DisplayOut {
  const DisplayOut({
    required this.memberId,
    required this.numbersDisplay,
    required this.summaryView,
    required this.updatedAt,
  });

  factory DisplayOut.fromJson(Map<String, Object?> json) =>
      _$DisplayOutFromJson(json);

  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'numbers_display')
  final DisplayOutNumbersDisplay numbersDisplay;
  @JsonKey(name: 'summary_view')
  final DisplayOutSummaryView summaryView;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$DisplayOutToJson(this);
}
