// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'weight_out.dart';

part 'weights_out.g.dart';

@JsonSerializable()
class WeightsOut {
  const WeightsOut({required this.items, required this.numbersHidden});

  factory WeightsOut.fromJson(Map<String, Object?> json) =>
      _$WeightsOutFromJson(json);

  final List<WeightOut> items;
  @JsonKey(name: 'numbers_hidden')
  final bool numbersHidden;

  Map<String, Object?> toJson() => _$WeightsOutToJson(this);
}
