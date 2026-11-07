// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum DisplayOutNumbersDisplay {
  /// The name has been replaced because it contains a keyword. Original name: `show`.
  @JsonValue('show')
  valueShow('show'),
  @JsonValue('hide_energy')
  hideEnergy('hide_energy'),
  @JsonValue('hide_all')
  hideAll('hide_all'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const DisplayOutNumbersDisplay(this.json);

  factory DisplayOutNumbersDisplay.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<DisplayOutNumbersDisplay> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
