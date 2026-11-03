// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'label_scan_in.g.dart';

@JsonSerializable()
class LabelScanIn {
  const LabelScanIn({required this.path, this.barcode});

  factory LabelScanIn.fromJson(Map<String, Object?> json) =>
      _$LabelScanInFromJson(json);

  final String? barcode;
  final String path;

  Map<String, Object?> toJson() => _$LabelScanInToJson(this);
}
