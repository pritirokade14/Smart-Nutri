// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'consent_state.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ConsentState _$ConsentStateFromJson(Map<String, dynamic> json) => ConsentState(
  currentVersion: json['current_version'] as String,
  granted: json['granted'] as bool,
  needsUpdate: json['needs_update'] as bool,
  purpose: json['purpose'] as String,
  version: json['version'] as String?,
);

Map<String, dynamic> _$ConsentStateToJson(ConsentState instance) =>
    <String, dynamic>{
      'current_version': instance.currentVersion,
      'granted': instance.granted,
      'needs_update': instance.needsUpdate,
      'purpose': instance.purpose,
      'version': instance.version,
    };
