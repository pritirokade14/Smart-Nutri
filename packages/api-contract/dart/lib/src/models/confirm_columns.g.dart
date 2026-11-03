// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'confirm_columns.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ConfirmColumns _$ConfirmColumnsFromJson(Map<String, dynamic> json) =>
    ConfirmColumns(
      per100g: json['per_100g'] == null
          ? null
          : ColumnConfirm.fromJson(json['per_100g'] as Map<String, dynamic>),
      perServing: json['per_serving'] == null
          ? null
          : ColumnConfirm.fromJson(json['per_serving'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$ConfirmColumnsToJson(ConfirmColumns instance) =>
    <String, dynamic>{
      'per_100g': instance.per100g,
      'per_serving': instance.perServing,
    };
