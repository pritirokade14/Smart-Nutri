// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'follow_ups_alerts.dart';
import 'follow_ups_allergens.dart';
import 'follow_ups_conditions.dart';
import 'follow_ups_diet.dart';
import 'follow_ups_family_with.dart';
import 'follow_ups_gym_goal.dart';

part 'follow_ups.g.dart';

/// At most one short follow-up per type (decision 4). `weight_loss` has none.
///
/// These are the user's answers, stored as given. They never change a member: pre-fill only.
/// suggests member changes, which the user confirms (Task 2).
@JsonSerializable()
class FollowUps {
  const FollowUps({
    this.alerts,
    this.allergens,
    this.conditions,
    this.diet,
    this.familyWith,
    this.gymGoal,
  });

  factory FollowUps.fromJson(Map<String, Object?> json) =>
      _$FollowUpsFromJson(json);

  final List<FollowUpsAlerts>? alerts;
  final List<FollowUpsAllergens>? allergens;
  final List<FollowUpsConditions>? conditions;
  final FollowUpsDiet? diet;
  @JsonKey(name: 'family_with')
  final List<FollowUpsFamilyWith>? familyWith;
  @JsonKey(name: 'gym_goal')
  final FollowUpsGymGoal? gymGoal;

  Map<String, Object?> toJson() => _$FollowUpsToJson(this);
}
