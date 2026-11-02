// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analyze_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnalyzeRequest _$AnalyzeRequestFromJson(Map<String, dynamic> json) =>
    AnalyzeRequest(
      language: json['language'] == null
          ? AnalyzeRequestLanguage.en
          : AnalyzeRequestLanguage.fromJson(json['language'] as String),
      barcode: json['barcode'] as String?,
      memberIds: (json['member_ids'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      productId: json['product_id'] as String?,
    );

Map<String, dynamic> _$AnalyzeRequestToJson(AnalyzeRequest instance) =>
    <String, dynamic>{
      'barcode': instance.barcode,
      'language': _$AnalyzeRequestLanguageEnumMap[instance.language]!,
      'member_ids': instance.memberIds,
      'product_id': instance.productId,
    };

const _$AnalyzeRequestLanguageEnumMap = {
  AnalyzeRequestLanguage.en: 'en',
  AnalyzeRequestLanguage.hi: 'hi',
  AnalyzeRequestLanguage.mr: 'mr',
  AnalyzeRequestLanguage.$unknown: r'$unknown',
};
