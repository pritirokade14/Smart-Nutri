// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'consent_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ConsentIn _$ConsentInFromJson(Map<String, dynamic> json) => ConsentIn(
  granted: json['granted'] as bool,
  purpose: ConsentInPurpose.fromJson(json['purpose'] as String),
  version: json['version'] as String,
);

Map<String, dynamic> _$ConsentInToJson(ConsentIn instance) => <String, dynamic>{
  'granted': instance.granted,
  'purpose': _$ConsentInPurposeEnumMap[instance.purpose]!,
  'version': instance.version,
};

const _$ConsentInPurposeEnumMap = {
  ConsentInPurpose.terms: 'terms',
  ConsentInPurpose.healthData: 'health_data',
  ConsentInPurpose.aiProcessing: 'ai_processing',
  ConsentInPurpose.$unknown: r'$unknown',
};
