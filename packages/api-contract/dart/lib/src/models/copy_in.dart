// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'copy_in.g.dart';

/// Copy one meal (``from_slot_id``) or the whole day (no ``from_slot_id``) onto another day.
///
/// ``client_id`` is required: each copy's own id is derived from it and the source entry, so a.
/// retry (a lost response, a double tap) returns the same rows and creates nothing. An entry.
/// whose slot has since been archived needs an explicit ``to_slot_id``.
@JsonSerializable()
class CopyIn {
  const CopyIn({
    required this.clientId,
    required this.fromDate,
    required this.toDate,
    this.fromSlotId,
    this.memberId,
    this.toSlotId,
  });

  factory CopyIn.fromJson(Map<String, Object?> json) => _$CopyInFromJson(json);

  @JsonKey(name: 'client_id')
  final String clientId;
  @JsonKey(name: 'from_date')
  final DateTime fromDate;
  @JsonKey(name: 'from_slot_id')
  final String? fromSlotId;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'to_date')
  final DateTime toDate;
  @JsonKey(name: 'to_slot_id')
  final String? toSlotId;

  Map<String, Object?> toJson() => _$CopyInToJson(this);
}
