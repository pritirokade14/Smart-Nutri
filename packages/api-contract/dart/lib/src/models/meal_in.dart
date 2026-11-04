// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'meal_in.g.dart';

/// Log what a member ate. Exactly one product reference (own ``product_id``, or a.
/// ``barcode`` for Open Food Facts products) and exactly one portion (``grams`` or.
/// ``servings``; servings need the product's serving size).
///
/// ``client_id`` makes the call idempotent: posting the same id again (an offline retry).
/// returns the stored log with 200 and never creates a second row.
@JsonSerializable()
class MealIn {
  const MealIn({
    required this.memberId,
    this.barcode,
    this.clientId,
    this.eatenAt,
    this.grams,
    this.productId,
    this.servings,
  });

  factory MealIn.fromJson(Map<String, Object?> json) => _$MealInFromJson(json);

  final String? barcode;
  @JsonKey(name: 'client_id')
  final String? clientId;

  /// Timezone-aware. Default: now. At most 5 minutes ahead, at most 30 days ago.
  @JsonKey(name: 'eaten_at')
  final DateTime? eatenAt;
  final num? grams;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'product_id')
  final String? productId;
  final num? servings;

  Map<String, Object?> toJson() => _$MealInToJson(this);
}
