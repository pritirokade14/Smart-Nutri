// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'favourite_log_in.g.dart';

/// Log a favourite meal again. ``client_id`` is required: each entry's own id is derived.
/// from it, so a retry returns the same rows with 200 and creates nothing.
@JsonSerializable()
class FavouriteLogIn {
  const FavouriteLogIn({
    required this.clientId,
    this.localDate,
    this.mealSlotId,
  });

  factory FavouriteLogIn.fromJson(Map<String, Object?> json) =>
      _$FavouriteLogInFromJson(json);

  @JsonKey(name: 'client_id')
  final String clientId;

  /// Log onto this local day (at most 30 days ago, not in future).
  @JsonKey(name: 'local_date')
  final DateTime? localDate;

  /// Default: the server's pick
  @JsonKey(name: 'meal_slot_id')
  final String? mealSlotId;

  Map<String, Object?> toJson() => _$FavouriteLogInToJson(this);
}
