// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'methodology_section.g.dart';

/// One part of "How we score". Clients render `methodology.section.<id>.*` strings; the.
/// API sends no prose.
@JsonSerializable()
class MethodologySection {
  const MethodologySection({
    required this.id,
    required this.rationaleSources,
    required this.thresholdSources,
    required this.thresholds,
  });

  factory MethodologySection.fromJson(Map<String, Object?> json) =>
      _$MethodologySectionFromJson(json);

  final String id;

  /// Source ids for why the rule exists. Null as for threshold_sources.
  @JsonKey(name: 'rationale_sources')
  final List<String>? rationaleSources;

  /// Source ids for the numbers. Null: a member preference with nothing to cite.
  @JsonKey(name: 'threshold_sources')
  final List<String>? thresholdSources;

  /// The live rule values from the rules engine config (shape differs per section). Never written by hand.
  final dynamic thresholds;

  Map<String, Object?> toJson() => _$MethodologySectionToJson(this);
}
