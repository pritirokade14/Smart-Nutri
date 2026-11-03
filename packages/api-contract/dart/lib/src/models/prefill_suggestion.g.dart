// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'prefill_suggestion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PrefillSuggestion _$PrefillSuggestionFromJson(Map<String, dynamic> json) =>
    PrefillSuggestion(
      changes: (json['changes'] as List<dynamic>)
          .map((e) => PrefillChange.fromJson(e as Map<String, dynamic>))
          .toList(),
      goalChoice: (json['goal_choice'] as List<dynamic>?)
          ?.map((e) => PrefillSuggestionGoalChoice.fromJson(e as String))
          .toList(),
      memberId: json['member_id'] as String,
      needsHealthConsent: json['needs_health_consent'] as bool,
    );

Map<String, dynamic> _$PrefillSuggestionToJson(PrefillSuggestion instance) =>
    <String, dynamic>{
      'changes': instance.changes,
      'goal_choice': instance.goalChoice
          ?.map((e) => _$PrefillSuggestionGoalChoiceEnumMap[e]!)
          .toList(),
      'member_id': instance.memberId,
      'needs_health_consent': instance.needsHealthConsent,
    };

const _$PrefillSuggestionGoalChoiceEnumMap = {
  PrefillSuggestionGoalChoice.healthyEating: 'healthy_eating',
  PrefillSuggestionGoalChoice.weightLoss: 'weight_loss',
  PrefillSuggestionGoalChoice.weightGain: 'weight_gain',
  PrefillSuggestionGoalChoice.buildMuscle: 'build_muscle',
  PrefillSuggestionGoalChoice.$unknown: r'$unknown',
};
