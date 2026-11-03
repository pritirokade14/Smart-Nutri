// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'draft_confirm.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DraftConfirm _$DraftConfirmFromJson(Map<String, dynamic> json) => DraftConfirm(
  basisRequired: json['basis_required'] as bool,
  categoryRequired: json['category_required'] as bool,
  categorySuggestion: json['category_suggestion'] as String?,
  columns: ConfirmColumns.fromJson(json['columns'] as Map<String, dynamic>),
);

Map<String, dynamic> _$DraftConfirmToJson(DraftConfirm instance) =>
    <String, dynamic>{
      'basis_required': instance.basisRequired,
      'category_required': instance.categoryRequired,
      'category_suggestion': instance.categorySuggestion,
      'columns': instance.columns,
    };
