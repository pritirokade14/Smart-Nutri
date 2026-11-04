// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'column_confirm_confirm_fields.dart';

part 'column_confirm.g.dart';

/// What to ask when the user saves with this `basis` (`ProductCreate.basis`).
@JsonSerializable()
class ColumnConfirm {
  const ColumnConfirm({
    required this.confirmFields,
    required this.printed,
    required this.servingRequired,
    required this.shared,
    required this.sodiumUnitRequired,
  });

  factory ColumnConfirm.fromJson(Map<String, Object?> json) =>
      _$ColumnConfirmFromJson(json);

  /// Fields that need an explicit tick (`ProductCreate.confirmed_fields`) when this basis is saved; an unticked one is stored as null. `serving_size_g`, when listed and unticked on a per-serving or derived save, makes every nutrient null. Sodium is never listed when `sodium_unit_required` (the unit pick confirms it).
  @JsonKey(name: 'confirm_fields')
  final List<ColumnConfirmConfirmFields> confirmFields;

  /// The draft column of this name holds printed engine values (`per_100g` of a `derived_from_serving` draft never does: those numbers were calculated).
  final bool printed;

  /// Saving this basis stores nutrient values only with a confirmed `serving_size_g` (`needs_serving_confirmation`, R19): keep save disabled until the serving size is confirmed (ticked or edited). Server-side, an unconfirmed serving still stores every nutrient as null.
  @JsonKey(name: 'serving_required')
  final bool servingRequired;

  /// On a `basis_mismatch` draft, this is the only printed column: show its values whichever basis the user picks (its basis is the doubt).
  final bool shared;

  /// Show a mg/g picker for sodium: `ProductCreate.sodium_unit` must be `mg` or `g` (never null) whenever the saved sodium is not null, else 422 `body.sodium_unit`. Set when sodium was printed without a unit (`unit_unconfirmed`) or as an implausibly low mg value with no salt to check it (`sodium_unit_suspect`).
  @JsonKey(name: 'sodium_unit_required')
  final bool sodiumUnitRequired;

  Map<String, Object?> toJson() => _$ColumnConfirmToJson(this);
}
