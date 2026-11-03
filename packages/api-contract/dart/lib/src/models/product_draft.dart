// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'draft_nutrients.dart';
import 'product_draft_category.dart';
import 'product_draft_engine_withheld.dart';
import 'product_draft_positive_suppressed.dart';
import 'product_draft_veg_mark.dart';

part 'product_draft.g.dart';

/// A normalised extraction awaiting user confirmation. Never saved as-is.
@JsonSerializable()
class ProductDraft {
  const ProductDraft({
    required this.allergenStatement,
    required this.brand,
    required this.category,
    required this.claims,
    required this.confidence,
    required this.derivedFromServing,
    required this.engineWithheld,
    required this.ingredients,
    required this.mayContainStatement,
    required this.name,
    required this.per100g,
    required this.perServing,
    required this.positiveSuppressed,
    required this.servingSizeG,
    required this.vegMark,
    required this.warnings,
  });

  factory ProductDraft.fromJson(Map<String, Object?> json) =>
      _$ProductDraftFromJson(json);

  @JsonKey(name: 'allergen_statement')
  final String? allergenStatement;
  final String? brand;
  final ProductDraftCategory category;
  final List<String> claims;
  final num confidence;
  @JsonKey(name: 'derived_from_serving')
  final bool derivedFromServing;
  @JsonKey(name: 'engine_withheld')
  final List<ProductDraftEngineWithheld> engineWithheld;
  final List<String> ingredients;
  @JsonKey(name: 'may_contain_statement')
  final String? mayContainStatement;
  final String? name;
  @JsonKey(name: 'per_100g')
  final DraftNutrients per100g;
  @JsonKey(name: 'per_serving')
  final DraftNutrients? perServing;
  @JsonKey(name: 'positive_suppressed')
  final List<ProductDraftPositiveSuppressed> positiveSuppressed;
  @JsonKey(name: 'serving_size_g')
  final num? servingSizeG;
  @JsonKey(name: 'veg_mark')
  final ProductDraftVegMark? vegMark;
  final List<String> warnings;

  Map<String, Object?> toJson() => _$ProductDraftToJson(this);
}
