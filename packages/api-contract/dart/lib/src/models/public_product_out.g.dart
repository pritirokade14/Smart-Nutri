// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'public_product_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PublicProductOut _$PublicProductOutFromJson(Map<String, dynamic> json) =>
    PublicProductOut(
      product: ProductOut.fromJson(json['product'] as Map<String, dynamic>),
      report: json['report'],
      scoreLabel: json['score_label'] as String,
    );

Map<String, dynamic> _$PublicProductOutToJson(PublicProductOut instance) =>
    <String, dynamic>{
      'product': instance.product,
      'report': instance.report,
      'score_label': instance.scoreLabel,
    };
