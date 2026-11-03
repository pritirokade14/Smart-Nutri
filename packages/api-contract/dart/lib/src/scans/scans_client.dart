// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/label_scan_in.dart';
import '../models/scan_draft_out.dart';
import '../models/upload_url_in.dart';
import '../models/upload_url_out.dart';

part 'scans_client.g.dart';

@RestApi()
abstract class ScansClient {
  factory ScansClient(Dio dio, {String? baseUrl}) = _ScansClient;

  /// Scans Create Label.
  ///
  /// Extract an unconfirmed draft from an uploaded label photo.
  ///
  /// Rate-limited per account (`rate_limited_scans`), counting only paid extractions: the.
  /// same image bytes again (from any account) reuse the stored draft for free.
  @POST('/v1/scans/label')
  Future<ScanDraftOut> scansCreateLabel({@Body() required LabelScanIn body});

  /// Scans Create Upload Url.
  ///
  /// A signed URL to PUT one label photo into the caller's private folder (no DB write).
  @POST('/v1/scans/upload-url')
  Future<UploadUrlOut> scansCreateUploadUrl({
    @Body() required UploadUrlIn body,
  });
}
