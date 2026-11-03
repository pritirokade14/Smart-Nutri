// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum MemberOutCustomAlerts {
  @JsonValue('palm_oil')
  palmOil('palm_oil'),
  @JsonValue('maida')
  maida('maida'),
  @JsonValue('added_sugar')
  addedSugar('added_sugar'),
  @JsonValue('artificial_sweetener')
  artificialSweetener('artificial_sweetener'),
  @JsonValue('msg')
  msg('msg'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const MemberOutCustomAlerts(this.json);

  factory MemberOutCustomAlerts.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<MemberOutCustomAlerts> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
