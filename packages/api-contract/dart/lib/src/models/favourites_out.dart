// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'favourite_out.dart';

part 'favourites_out.g.dart';

@JsonSerializable()
class FavouritesOut {
  const FavouritesOut({required this.items});

  factory FavouritesOut.fromJson(Map<String, Object?> json) =>
      _$FavouritesOutFromJson(json);

  final List<FavouriteOut> items;

  Map<String, Object?> toJson() => _$FavouritesOutToJson(this);
}
