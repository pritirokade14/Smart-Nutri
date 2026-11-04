// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'methodology.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Methodology _$MethodologyFromJson(Map<String, dynamic> json) => Methodology(
  language: MethodologyLanguage.fromJson(json['language'] as String),
  pendingClinicianReview: json['pending_clinician_review'] as bool,
  sections: (json['sections'] as List<dynamic>)
      .map((e) => MethodologySection.fromJson(e as Map<String, dynamic>))
      .toList(),
  sources: (json['sources'] as List<dynamic>)
      .map((e) => MethodologySource.fromJson(e as Map<String, dynamic>))
      .toList(),
  version: json['version'] as String,
);

Map<String, dynamic> _$MethodologyToJson(Methodology instance) =>
    <String, dynamic>{
      'language': _$MethodologyLanguageEnumMap[instance.language]!,
      'pending_clinician_review': instance.pendingClinicianReview,
      'sections': instance.sections,
      'sources': instance.sources,
      'version': instance.version,
    };

const _$MethodologyLanguageEnumMap = {
  MethodologyLanguage.en: 'en',
  MethodologyLanguage.hi: 'hi',
  MethodologyLanguage.mr: 'mr',
  MethodologyLanguage.$unknown: r'$unknown',
};
