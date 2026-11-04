// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'methodology_section.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MethodologySection _$MethodologySectionFromJson(Map<String, dynamic> json) =>
    MethodologySection(
      id: json['id'] as String,
      rationaleSources: (json['rationale_sources'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      thresholdSources: (json['threshold_sources'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      thresholds: json['thresholds'],
    );

Map<String, dynamic> _$MethodologySectionToJson(MethodologySection instance) =>
    <String, dynamic>{
      'id': instance.id,
      'rationale_sources': instance.rationaleSources,
      'threshold_sources': instance.thresholdSources,
      'thresholds': instance.thresholds,
    };
