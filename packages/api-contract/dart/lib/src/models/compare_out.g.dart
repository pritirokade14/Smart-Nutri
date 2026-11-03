// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'compare_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CompareOut _$CompareOutFromJson(Map<String, dynamic> json) => CompareOut(
  a: CompareSide.fromJson(json['a'] as Map<String, dynamic>),
  b: CompareSide.fromJson(json['b'] as Map<String, dynamic>),
  better: CompareBetter.fromJson(json['better'] as Map<String, dynamic>),
);

Map<String, dynamic> _$CompareOutToJson(CompareOut instance) =>
    <String, dynamic>{
      'a': instance.a,
      'b': instance.b,
      'better': instance.better,
    };
