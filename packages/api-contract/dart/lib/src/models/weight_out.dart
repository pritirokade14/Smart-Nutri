// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'weight_out.g.dart';

@JsonSerializable()
class WeightOut {
  const WeightOut({
    required this.clientId,
    required this.date,
    required this.measuredAt,
    required this.numbersHidden,
    required this.source,
    required this.weightKg,
  });

  factory WeightOut.fromJson(Map<String, Object?> json) =>
      _$WeightOutFromJson(json);

  @JsonKey(name: 'client_id')
  final String? clientId;
  final DateTime date;
  @JsonKey(name: 'measured_at')
  final DateTime measuredAt;
  @JsonKey(name: 'numbers_hidden')
  final bool numbersHidden;
  final String source;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$WeightOutToJson(this);
}
