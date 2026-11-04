// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_in_conditions.dart';
import 'member_in_custom_alerts.dart';
import 'member_in_diet.dart';
import 'member_in_goal.dart';
import 'member_in_relation.dart';
import 'member_in_sex.dart';

part 'member_in.g.dart';

/// Create a family member. The account holder (relation `self`) already exists.
@JsonSerializable()
class MemberIn {
  const MemberIn({
    required this.birthYear,
    required this.name,
    required this.relation,
    this.goal,
    this.heightCm,
    this.sex,
    this.weightKg,
    this.allergens = const [],
    this.conditions = const [],
    this.customAlerts = const [],
    this.diet = MemberInDiet.nonVeg,
  });

  factory MemberIn.fromJson(Map<String, Object?> json) =>
      _$MemberInFromJson(json);

  final List<String> allergens;
  @JsonKey(name: 'birth_year')
  final int birthYear;
  final List<MemberInConditions> conditions;
  @JsonKey(name: 'custom_alerts')
  final List<MemberInCustomAlerts> customAlerts;
  final MemberInDiet diet;
  final MemberInGoal? goal;
  @JsonKey(name: 'height_cm')
  final num? heightCm;
  final String name;
  final MemberInRelation relation;
  final MemberInSex? sex;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$MemberInToJson(this);
}
