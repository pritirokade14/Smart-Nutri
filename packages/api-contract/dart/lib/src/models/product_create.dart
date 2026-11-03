// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'nutrients_out.dart';
import 'product_create_category.dart';
import 'product_create_confirmed_fields.dart';
import 'product_create_veg_mark.dart';

part 'product_create.g.dart';

/// A product the user confirmed on the label-confirm screen, or typed by hand.
///
/// With ``scan_id`` the values come from that label scan's draft (source ``label``, the.
/// draft's extraction confidence); without it the entry is manual (source ``user``,.
/// confidence 1.0). Blank values are null, never 0. Text keeps its script (Devanagari stays.
/// Devanagari); only surrounding whitespace is trimmed and blank items are dropped.
@JsonSerializable()
class ProductCreate {
  const ProductCreate({
    required this.name,
    required this.per100g,
    this.category = ProductCreateCategory.general,
    this.claims = const [],
    this.confirmedFields = const [],
    this.ingredients = const [],
    this.allergenStatement,
    this.barcode,
    this.brand,
    this.mayContainStatement,
    this.scanId,
    this.servingSizeG,
    this.vegMark,
  });

  factory ProductCreate.fromJson(Map<String, Object?> json) =>
      _$ProductCreateFromJson(json);

  @JsonKey(name: 'allergen_statement')
  final String? allergenStatement;
  final String? barcode;
  final String? brand;
  final ProductCreateCategory category;
  final List<String> claims;
  @JsonKey(name: 'confirmed_fields')
  final List<ProductCreateConfirmedFields> confirmedFields;
  final List<String> ingredients;
  @JsonKey(name: 'may_contain_statement')
  final String? mayContainStatement;
  final String name;
  @JsonKey(name: 'per_100g')
  final NutrientsOut per100g;
  @JsonKey(name: 'scan_id')
  final String? scanId;
  @JsonKey(name: 'serving_size_g')
  final num? servingSizeG;
  @JsonKey(name: 'veg_mark')
  final ProductCreateVegMark? vegMark;

  Map<String, Object?> toJson() => _$ProductCreateToJson(this);
}
