// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'food_hit.dart';

part 'food_search_out.g.dart';

@JsonSerializable()
class FoodSearchOut {
  const FoodSearchOut({
    required this.failedSources,
    required this.items,
    required this.partial,
  });

  factory FoodSearchOut.fromJson(Map<String, Object?> json) =>
      _$FoodSearchOutFromJson(json);

  @JsonKey(name: 'failed_sources')
  final List<String> failedSources;
  final List<FoodHit> items;

  /// true when a source (Open Food Facts) could not answer
  final bool partial;

  Map<String, Object?> toJson() => _$FoodSearchOutToJson(this);
}
