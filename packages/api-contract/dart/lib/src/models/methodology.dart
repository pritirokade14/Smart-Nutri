// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'methodology_language.dart';
import 'methodology_section.dart';
import 'methodology_source.dart';

part 'methodology.g.dart';

@JsonSerializable()
class Methodology {
  const Methodology({
    required this.language,
    required this.pendingClinicianReview,
    required this.sections,
    required this.sources,
    required this.version,
  });

  factory Methodology.fromJson(Map<String, Object?> json) =>
      _$MethodologyFromJson(json);

  final MethodologyLanguage language;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;
  final List<MethodologySection> sections;
  final List<MethodologySource> sources;

  /// Changes whenever any shown value changes.
  final String version;

  Map<String, Object?> toJson() => _$MethodologyToJson(this);
}
