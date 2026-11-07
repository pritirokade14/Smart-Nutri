// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'custom_portion_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CustomPortionIn _$CustomPortionInFromJson(Map<String, dynamic> json) =>
    CustomPortionIn(
      gramsPerUnit: json['grams_per_unit'] as num,
      unit: CustomPortionInUnit.fromJson(json['unit'] as String),
    );

Map<String, dynamic> _$CustomPortionInToJson(CustomPortionIn instance) =>
    <String, dynamic>{
      'grams_per_unit': instance.gramsPerUnit,
      'unit': _$CustomPortionInUnitEnumMap[instance.unit]!,
    };

const _$CustomPortionInUnitEnumMap = {
  CustomPortionInUnit.g: 'g',
  CustomPortionInUnit.ml: 'ml',
  CustomPortionInUnit.serving: 'serving',
  CustomPortionInUnit.piece: 'piece',
  CustomPortionInUnit.pieceSmall: 'piece_small',
  CustomPortionInUnit.pieceMedium: 'piece_medium',
  CustomPortionInUnit.pieceLarge: 'piece_large',
  CustomPortionInUnit.roti: 'roti',
  CustomPortionInUnit.slice: 'slice',
  CustomPortionInUnit.katori: 'katori',
  CustomPortionInUnit.katoriSmall: 'katori_small',
  CustomPortionInUnit.katoriMedium: 'katori_medium',
  CustomPortionInUnit.katoriLarge: 'katori_large',
  CustomPortionInUnit.cup: 'cup',
  CustomPortionInUnit.glass: 'glass',
  CustomPortionInUnit.tbsp: 'tbsp',
  CustomPortionInUnit.tsp: 'tsp',
  CustomPortionInUnit.$unknown: r'$unknown',
};
