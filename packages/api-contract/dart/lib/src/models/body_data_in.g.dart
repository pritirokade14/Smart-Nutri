// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'body_data_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BodyDataIn _$BodyDataInFromJson(Map<String, dynamic> json) => BodyDataIn(
  birthYear: (json['birth_year'] as num?)?.toInt(),
  bodyFatPct: json['body_fat_pct'] as num?,
  heightCm: json['height_cm'] as num?,
  sex: json['sex'] == null
      ? null
      : BodyDataInSex.fromJson(json['sex'] as String),
  weightKg: json['weight_kg'] as num?,
);

Map<String, dynamic> _$BodyDataInToJson(BodyDataIn instance) =>
    <String, dynamic>{
      'birth_year': instance.birthYear,
      'body_fat_pct': instance.bodyFatPct,
      'height_cm': instance.heightCm,
      'sex': _$BodyDataInSexEnumMap[instance.sex],
      'weight_kg': instance.weightKg,
    };

const _$BodyDataInSexEnumMap = {
  BodyDataInSex.female: 'female',
  BodyDataInSex.male: 'male',
  BodyDataInSex.other: 'other',
  BodyDataInSex.$unknown: r'$unknown',
};
