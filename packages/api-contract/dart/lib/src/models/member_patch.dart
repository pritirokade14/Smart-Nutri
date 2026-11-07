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
///
/// `body_fat_pct: null` also means "unchanged", NOT "clear" (Plan 10, Ruling D3: the Dart.
/// client sends it as null on every unrelated edit and would wipe the value). To clear it send.
/// `clear_body_fat_pct: true`; sending a value and the clear flag together is a 422.
@JsonSerializable()
class MemberPatch {
  const MemberPatch({
    this.clearBodyFatPct = false,
    this.allergens,
    this.birthYear,
    this.bodyFatPct,
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
  @JsonKey(name: 'body_fat_pct')
  final num? bodyFatPct;
  @JsonKey(name: 'clear_body_fat_pct')
  final bool clearBodyFatPct;
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
