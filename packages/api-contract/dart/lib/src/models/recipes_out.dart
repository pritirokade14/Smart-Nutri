// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'recipe_summary_out.dart';

part 'recipes_out.g.dart';

@JsonSerializable()
class RecipesOut {
  const RecipesOut({required this.items, required this.nextCursor});

  factory RecipesOut.fromJson(Map<String, Object?> json) =>
      _$RecipesOutFromJson(json);

  final List<RecipeSummaryOut> items;

  /// Opaque; pass back as `cursor`
  @JsonKey(name: 'next_cursor')
  final String? nextCursor;

  Map<String, Object?> toJson() => _$RecipesOutToJson(this);
}
