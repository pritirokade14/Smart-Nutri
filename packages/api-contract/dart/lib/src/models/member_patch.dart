// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_patch_conditions.dart';
import 'member_patch_custom_alerts.dart';
import 'member_patch_diet.dart';
import 'member_patch_goal.dart';
import 'member_patch_relation.dart';
import 'member_patch_sex.dart';

part 'member_patch.g.dart';

/// Change only the fields sent. `relation` can't become `self`, or change on the primary.
///
/// `null` clears `sex`, `height_cm`, `weight_kg` and `goal`. For every other field `null`.
/// means "unchanged" (the generated Dart client sends every field, unset ones as null), so.
/// `birth_year` can never be cleared.
@JsonSerializable()
class MemberPatch {
  const MemberPatch({
    this.allergens,
    this.birthYear,
    this.conditions,
    this.customAlerts,
    this.diet,
    this.goal,
    this.heightCm,
    this.name,
    this.relation,
    this.sex,
    this.weightKg,
  });

  factory MemberPatch.fromJson(Map<String, Object?> json) =>
      _$MemberPatchFromJson(json);

  final List<String>? allergens;
  @JsonKey(name: 'birth_year')
  final int? birthYear;
  final List<MemberPatchConditions>? conditions;
  @JsonKey(name: 'custom_alerts')
  final List<MemberPatchCustomAlerts>? customAlerts;
  final MemberPatchDiet? diet;
  final MemberPatchGoal? goal;
  @JsonKey(name: 'height_cm')
  final num? heightCm;
  final String? name;
  final MemberPatchRelation? relation;
  final MemberPatchSex? sex;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$MemberPatchToJson(this);
}
