// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'quick_in.dart';

part 'meal_in.g.dart';

/// Log what a member ate. Exactly one food reference (own ``product_id``, a ``barcode``.
/// for Open Food Facts products, or ``quick``) and, except for a quick add, exactly one.
/// portion (``grams`` or ``servings``; servings need the product's serving size).
///
/// ``member_id`` defaults to the primary member. ``meal_slot_id`` defaults to the slot the.
/// server picks from the local time. ``local_date`` logs onto a past day (``eaten_at`` becomes.
/// that date at the current local clock time, capped at now); it cannot be sent together with.
/// ``eaten_at``.
///
/// ``client_id`` makes the call idempotent: posting the same id again (an offline retry).
/// returns the stored log with 200 and never creates a second row.
@JsonSerializable()
class MealIn {
  const MealIn({
    this.barcode,
    this.clientId,
    this.eatenAt,
    this.grams,
    this.localDate,
    this.mealSlotId,
    this.memberId,
    this.productId,
    this.quick,
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

  /// Log onto this local day (at most 30 days ago, not in future).
  @JsonKey(name: 'local_date')
  final DateTime? localDate;
  @JsonKey(name: 'meal_slot_id')
  final String? mealSlotId;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'product_id')
  final String? productId;
  final QuickIn? quick;
  final num? servings;

  Map<String, Object?> toJson() => _$MealInToJson(this);
}
