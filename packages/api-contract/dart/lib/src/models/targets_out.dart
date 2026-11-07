// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'numbers_hidden.dart';
import 'rate_out.dart';
import 'targets_explanation.dart';
import 'targets_out_basis.dart';
import 'targets_out_direction.dart';
import 'targets_out_status.dart';

part 'targets_out.g.dart';

/// Spec 6.1 plus `rate_options` and `unusual_fields` (Ruling D5).
@JsonSerializable()
class TargetsOut {
  const TargetsOut({
    required this.basis,
    required this.carbsG,
    required this.date,
    required this.direction,
    required this.energyKcal,
    required this.explanation,
    required this.fatG,
    required this.flags,
    required this.memberId,
    required this.missingFields,
    required this.numbersHidden,
    required this.proteinG,
    required this.rate,
    required this.rateOptions,
    required this.sources,
    required this.status,
    required this.unusualFields,
    this.pendingClinicianReview = true,
  });

  factory TargetsOut.fromJson(Map<String, Object?> json) =>
      _$TargetsOutFromJson(json);

  final TargetsOutBasis? basis;
  @JsonKey(name: 'carbs_g')
  final int? carbsG;
  final DateTime date;
  final TargetsOutDirection? direction;
  @JsonKey(name: 'energy_kcal')
  final int? energyKcal;
  final TargetsExplanation? explanation;
  @JsonKey(name: 'fat_g')
  final int? fatG;
  final List<String> flags;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'missing_fields')
  final List<String> missingFields;
  @JsonKey(name: 'numbers_hidden')
  final NumbersHidden numbersHidden;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;
  @JsonKey(name: 'protein_g')
  final int? proteinG;
  final RateOut? rate;
  @JsonKey(name: 'rate_options')
  final List<RateOut> rateOptions;
  final List<String> sources;
  final TargetsOutStatus status;
  @JsonKey(name: 'unusual_fields')
  final List<String> unusualFields;

  Map<String, Object?> toJson() => _$TargetsOutToJson(this);
}
