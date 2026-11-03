// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'printed_nutrients.dart';
import 'product_create_basis.dart';
import 'product_create_category.dart';
import 'product_create_confirmed_fields.dart';
import 'product_create_sodium_unit.dart';
import 'product_create_veg_mark.dart';

part 'product_create.g.dart';

/// A product the user confirmed on the label-confirm screen, or typed by hand.
///
/// **The server does all nutrient arithmetic; the client only transcribes what the pack.
/// prints and records the user's explicit choices.** The stored per-100 g values are:.
///
/// 1. `nutrients` as sent, with `sodium_mg` multiplied by 1000 when `sodium_unit` is `g`;.
/// 2. then, when `basis` is `per_serving`, every value x 100 / `serving_size_g`;.
/// 3. then, for a scan save, values the draft holds back are set to null unless confirmed.
///    (`confirmed_fields`, below);.
/// 4. then the engine's plausibility check runs on exactly the values that will be stored.
///    (422 `implausible_value`), including `serving_size_g` only when it will be stored or.
///    used for conversion. Values are never rounded.
///
/// With `scan_id` the values come from that label scan (source `label`, the extraction.
/// confidence, which user edits never raise); without it the entry is manual (source.
/// `user`, confidence 1.0, values taken as typed). For a scan save the server re-runs its.
/// current normaliser on the stored raw extraction (R19), so the warnings it applies can be.
/// stricter than the draft the client showed; scans without a stored raw extraction use the.
/// stored draft. Text keeps its script (Devanagari stays Devanagari); only surrounding.
/// whitespace is trimmed and blank items are dropped.
///
/// Scan-save rules (422 `validation_error` with `details.fields` naming the field):.
/// - `category` and `basis` are always required (the user must pick them; nothing defaults).
/// - (R19) `sodium_unit` must be `mg` or `g` (not null) whenever the draft has ANY.
///   `unit_unconfirmed:*.sodium_mg` warning (either column, whichever `basis` is chosen) and.
///   `nutrients.sodium_mg` is not null; else 422 `["body.sodium_unit"]`. Listing `sodium_mg`.
///   in `confirmed_fields` never stands in for the unit. A non-null unit confirms sodium.
/// - (R19) With `basis` `per_serving`, or whenever the draft was `derived_from_serving`.
///   (with or without `basis_mismatch`), every nutrient is stored only if `confirmed_fields`.
///   contains `serving_size_g` (the user checked the serving size); otherwise all are.
///   stored null and the serving size is neither used nor checked.
/// - (R18) The stored `serving_size_g` is the sent value only if `confirmed_fields` contains.
///   `serving_size_g`; otherwise it is stored null (unknown) and the engine falls back to.
///   per-100 g. A manual entry (no `scan_id`) stores the serving size as typed.
/// - On a `basis_mismatch` draft the explicit `basis` confirms the values sent. (R19) An.
///   upper-bound ("<X") protein or fibre on EITHER printed column is stored only if listed.
///   in `confirmed_fields`, and a unit-less sodium still needs `sodium_unit`.
@JsonSerializable()
class ProductCreate {
  const ProductCreate({
    required this.basis,
    required this.category,
    required this.name,
    required this.nutrients,
    this.claims = const [],
    this.confirmedFields = const [],
    this.ingredients = const [],
    this.allergenStatement,
    this.barcode,
    this.brand,
    this.mayContainStatement,
    this.scanId,
    this.servingSizeG,
    this.sodiumUnit,
    this.vegMark,
  });

  factory ProductCreate.fromJson(Map<String, Object?> json) =>
      _$ProductCreateFromJson(json);

  @JsonKey(name: 'allergen_statement')
  final String? allergenStatement;
  final String? barcode;

  /// Required: which printed column `nutrients` was transcribed from. `per_100g` means per 100 g or 100 ml; `per_serving` means per `serving_size_g`, and the server converts to per 100 g.
  final ProductCreateBasis basis;
  final String? brand;

  /// Required: the user's explicit choice (drinks are judged on drink limits).
  final ProductCreateCategory category;
  final List<String> claims;

  /// Scan saves only: what the user explicitly confirmed. A nutrient the draft lists in `engine_withheld`, or an upper-bound ("<0.1 g") protein or fibre on either printed column (R19), is stored only when listed here, else null. `serving_size_g` confirms the serving size and is required for any value of a per-serving save or a `derived_from_serving` draft to be stored (R19); an unconfirmed scanned serving size is stored as null (R18). Listing `sodium_mg` never replaces `sodium_unit`.
  @JsonKey(name: 'confirmed_fields')
  final List<ProductCreateConfirmedFields> confirmedFields;
  final List<String> ingredients;
  @JsonKey(name: 'may_contain_statement')
  final String? mayContainStatement;
  final String name;

  /// The chosen column as printed. The server converts it (see `basis`).
  final PrintedNutrients nutrients;

  /// The label scan this came from; null for manual entry.
  @JsonKey(name: 'scan_id')
  final String? scanId;

  /// Serving size in g (or ml). Required when `basis` is `per_serving`. For a scan save it is used for conversion and stored only when `confirmed_fields` lists it (R18); otherwise it is stored as null, and is not plausibility-checked because it is neither stored nor used (R19). A manual entry stores it as typed.
  @JsonKey(name: 'serving_size_g')
  final num? servingSizeG;

  /// The unit of `nutrients.sodium_mg`: null means mg (the unit is printed, or this is a manual entry in mg). `g` is converted to mg by the server. Send the user's explicit pick (`mg` or `g`, never null) whenever the scan draft has any `unit_unconfirmed:*.sodium_mg` warning (either column, whatever the basis) and sodium is not null, else 422 `body.sodium_unit` (R19). A non-null unit confirms sodium; `confirmed_fields` never replaces it.
  @JsonKey(name: 'sodium_unit')
  final ProductCreateSodiumUnit? sodiumUnit;
  @JsonKey(name: 'veg_mark')
  final ProductCreateVegMark? vegMark;

  Map<String, Object?> toJson() => _$ProductCreateToJson(this);
}
