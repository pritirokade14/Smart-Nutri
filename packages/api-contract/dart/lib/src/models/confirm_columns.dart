// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'column_confirm.dart';

part 'confirm_columns.g.dart';

/// The bases the user may save with; null = not offered for this draft.
@JsonSerializable()
class ConfirmColumns {
  const ConfirmColumns({required this.per100g, required this.perServing});

  factory ConfirmColumns.fromJson(Map<String, Object?> json) =>
      _$ConfirmColumnsFromJson(json);

  @JsonKey(name: 'per_100g')
  final ColumnConfirm? per100g;
  @JsonKey(name: 'per_serving')
  final ColumnConfirm? perServing;

  Map<String, Object?> toJson() => _$ConfirmColumnsToJson(this);
}
