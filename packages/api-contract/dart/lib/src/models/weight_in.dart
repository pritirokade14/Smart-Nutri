// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'weight_in.g.dart';

/// `weight_kg` is checked by the service (2 to 300, else 422 `weight_out_of_range`) and kept.
/// to 2 dp. A value outside 30 to 200, or far from the last weigh-in, needs `confirm_unusual`.
@JsonSerializable()
class WeightIn {
  const WeightIn({
    required this.weightKg,
    this.confirmUnusual = false,
    this.clientId,
    this.memberId,
  });

  factory WeightIn.fromJson(Map<String, Object?> json) =>
      _$WeightInFromJson(json);

  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'confirm_unusual')
  final bool confirmUnusual;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'weight_kg')
  final num weightKg;

  Map<String, Object?> toJson() => _$WeightInToJson(this);
}
