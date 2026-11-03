// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'confirm_columns.dart';

part 'draft_confirm.g.dart';

/// Server-computed confirm-screen hints (R21). Clients render these; they never.
/// re-derive the save rules. Computed from the draft itself, so always current.
@JsonSerializable()
class DraftConfirm {
  const DraftConfirm({
    required this.basisRequired,
    required this.categoryRequired,
    required this.columns,
  });

  factory DraftConfirm.fromJson(Map<String, Object?> json) =>
      _$DraftConfirmFromJson(json);

  /// Basis in doubt: offer both columns and never preselect a basis.
  @JsonKey(name: 'basis_required')
  final bool basisRequired;

  /// Category in doubt: never preselect; the user must pick a category.
  @JsonKey(name: 'category_required')
  final bool categoryRequired;
  final ConfirmColumns columns;

  Map<String, Object?> toJson() => _$DraftConfirmToJson(this);
}
