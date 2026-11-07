// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'recipe_summary_out.g.dart';

@JsonSerializable()
class RecipeSummaryOut {
  const RecipeSummaryOut({
    required this.id,
    required this.incompleteNutrients,
    required this.name,
    required this.servings,
    required this.updatedAt,
  });

  factory RecipeSummaryOut.fromJson(Map<String, Object?> json) =>
      _$RecipeSummaryOutFromJson(json);

  final String id;
  @JsonKey(name: 'incomplete_nutrients')
  final List<String> incompleteNutrients;
  final String name;
  final num? servings;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$RecipeSummaryOutToJson(this);
}
