// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'custom_food_out.dart';

part 'custom_foods_out.g.dart';

@JsonSerializable()
class CustomFoodsOut {
  const CustomFoodsOut({required this.items, required this.nextCursor});

  factory CustomFoodsOut.fromJson(Map<String, Object?> json) =>
      _$CustomFoodsOutFromJson(json);

  final List<CustomFoodOut> items;

  /// Opaque; pass back as `cursor` for the next page
  @JsonKey(name: 'next_cursor')
  final String? nextCursor;

  Map<String, Object?> toJson() => _$CustomFoodsOutToJson(this);
}
