// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'favourite_meal_in.g.dart';

/// Save the entries of one meal slot on one day as a named favourite meal. ``name`` is.
/// user text, 1 to 40 characters, kept exactly as typed.
@JsonSerializable()
class FavouriteMealIn {
  const FavouriteMealIn({
    required this.fromDate,
    required this.fromSlotId,
    required this.name,
    this.clientId,
    this.memberId,
  });

  factory FavouriteMealIn.fromJson(Map<String, Object?> json) =>
      _$FavouriteMealInFromJson(json);

  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'from_date')
  final DateTime fromDate;
  @JsonKey(name: 'from_slot_id')
  final String fromSlotId;
  @JsonKey(name: 'member_id')
  final String? memberId;
  final String name;

  Map<String, Object?> toJson() => _$FavouriteMealInToJson(this);
}
