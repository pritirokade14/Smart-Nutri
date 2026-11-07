// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'meal_out.dart';

part 'favourite_log_out.g.dart';

@JsonSerializable()
class FavouriteLogOut {
  const FavouriteLogOut({required this.created});

  factory FavouriteLogOut.fromJson(Map<String, Object?> json) =>
      _$FavouriteLogOutFromJson(json);

  /// The new entries, in the saved order
  final List<MealOut> created;

  Map<String, Object?> toJson() => _$FavouriteLogOutToJson(this);
}
