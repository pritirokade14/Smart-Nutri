// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_out_conditions.dart';
import 'member_out_custom_alerts.dart';
import 'member_out_diet.dart';
import 'member_out_goal.dart';
import 'member_out_relation.dart';
import 'member_out_sex.dart';

part 'member_out.g.dart';

@JsonSerializable()
class MemberOut {
  const MemberOut({
    required this.allergens,
    required this.birthYear,
    required this.conditions,
    required this.customAlerts,
    required this.diet,
    required this.goal,
    required this.heightCm,
    required this.id,
    required this.isPrimary,
    required this.name,
    required this.relation,
    required this.sex,
    required this.weightKg,
  });

  factory MemberOut.fromJson(Map<String, Object?> json) =>
      _$MemberOutFromJson(json);

  final List<String> allergens;
  @JsonKey(name: 'birth_year')
  final int? birthYear;
  final List<MemberOutConditions> conditions;
  @JsonKey(name: 'custom_alerts')
  final List<MemberOutCustomAlerts> customAlerts;
  final MemberOutDiet diet;
  final MemberOutGoal? goal;
  @JsonKey(name: 'height_cm')
  final num? heightCm;
  final String id;
  @JsonKey(name: 'is_primary')
  final bool isPrimary;
  final String name;
  final MemberOutRelation relation;
  final MemberOutSex? sex;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$MemberOutToJson(this);
}
