// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'display_in_numbers_display.dart';
import 'display_in_summary_view.dart';

part 'display_in.g.dart';

/// The eye toggle (Ruling D4): only these two fields change; null means unchanged.
@JsonSerializable()
class DisplayIn {
  const DisplayIn({this.memberId, this.numbersDisplay, this.summaryView});

  factory DisplayIn.fromJson(Map<String, Object?> json) =>
      _$DisplayInFromJson(json);

  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'numbers_display')
  final DisplayInNumbersDisplay? numbersDisplay;
  @JsonKey(name: 'summary_view')
  final DisplayInSummaryView? summaryView;

  Map<String, Object?> toJson() => _$DisplayInToJson(this);
}
