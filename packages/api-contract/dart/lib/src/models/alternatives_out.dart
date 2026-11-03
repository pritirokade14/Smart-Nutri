// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'alternative_out.dart';
import 'alternatives_out_reason.dart';

part 'alternatives_out.g.dart';

@JsonSerializable()
class AlternativesOut {
  const AlternativesOut({required this.items, required this.reason});

  factory AlternativesOut.fromJson(Map<String, Object?> json) =>
      _$AlternativesOutFromJson(json);

  /// At most 5. sort=grade: best grade first, then less sugar, then name. sort=protein: strictly more protein per 100 kcal than the source and a grade no worse; ok before caution before unknown, then most protein per 100 kcal, then grade, then name. Never a product the engine rates avoid for the member (sort=grade: member_id only; sort=protein: member_id or the primary member)
  final List<AlternativeOut> items;

  /// no_better_found also when every better product is avoid for the member; source_protein_unknown: sort=protein and the source has no protein per 100 kcal
  final AlternativesOutReason reason;

  Map<String, Object?> toJson() => _$AlternativesOutToJson(this);
}
