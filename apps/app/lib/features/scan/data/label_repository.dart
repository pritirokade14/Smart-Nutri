import 'dart:math' as math;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// The API's upload limit (`error.image_too_large` above it).
const int maxUploadBytes = 8 * 1024 * 1024;

/// The longest side of an uploaded label photo, in pixels.
const int maxUploadSide = 2000;

/// What [LabelRepository.scanLabel] is doing, for the progress text.
enum LabelPhase { uploading, reading }

/// A label-scan or product-save failure, by API error code (`error.<code>`),
/// or `network` when there was no response.
class LabelFailure implements Exception {
  const LabelFailure(this.code, {this.fields = const [], this.productId});

  final String code;

  /// Fields the API named (`details.fields`), without the `body.` prefix
  /// (e.g. `protein_g`, `serving_size_g`, `sodium_unit`).
  final List<String> fields;

  /// `product_exists`: the product the caller can already see, if given.
  final String? productId;

  @override
  String toString() => 'LabelFailure($code)';
}

/// Re-encodes a photo as JPEG with its longest side at most [maxUploadSide]
/// and at most [maxUploadBytes]. EXIF orientation is applied first, so the
/// label is upright. Throws `LabelFailure('unsupported_image')` for bytes that
/// are not a decodable image.
Future<Uint8List> compressForUpload(Uint8List bytes) async {
  final out = await compute(_compress, bytes);
  if (out == null) throw const LabelFailure('unsupported_image');
  if (out.length > maxUploadBytes) throw const LabelFailure('image_too_large');
  return out;
}

Uint8List? _compress(Uint8List bytes) {
  final decoded = img.decodeImage(bytes);
  if (decoded == null) return null;
  var image = img.bakeOrientation(decoded);
  final longest = math.max(image.width, image.height);
  if (longest > maxUploadSide) {
    image = image.width >= image.height
        ? img.copyResize(image, width: maxUploadSide)
        : img.copyResize(image, height: maxUploadSide);
  }
  var out = img.encodeJpg(image, quality: 85);
  for (final quality in const [70, 55, 40]) {
    if (out.length <= maxUploadBytes) break;
    out = img.encodeJpg(image, quality: quality);
  }
  return out;
}

typedef ImageCompressor = Future<Uint8List> Function(Uint8List bytes);

/// Label photo upload and extraction, and saving the confirmed product.
///
/// Returns API bodies unchanged: the draft is shown for the user to confirm,
/// and the saved values are converted and judged only by the API.
class LabelRepository {
  LabelRepository({
    required this._scans,
    required this._products,
    required this._uploadDio,
    this._compress = compressForUpload,
  });

  final ScansClient _scans;
  final ProductsClient _products;

  /// A plain Dio: the signed upload URL must not receive our bearer token.
  final Dio _uploadDio;
  final ImageCompressor _compress;

  /// compress → upload URL → PUT (no auth header) → `scans_create_label`.
  Future<ScanDraftOut> scanLabel(
    XFile photo, {
    String? barcode,
    void Function(LabelPhase phase)? onPhase,
  }) async {
    onPhase?.call(LabelPhase.uploading);
    final bytes = await _compress(await photo.readAsBytes());
    final target = await _call(
      () => _scans.scansCreateUploadUrl(
        body: const UploadUrlIn(ext: UploadUrlInExt.jpg),
      ),
    );
    await _put(target.uploadUrl, bytes);
    onPhase?.call(LabelPhase.reading);
    return _call(
      () => _scans.scansCreateLabel(
        body: LabelScanIn(path: target.path, barcode: barcode),
      ),
    );
  }

  /// `products_create`; the caller then analyses the returned product_id.
  Future<ProductOut> saveDraft(ProductCreate body) =>
      _call(() => _products.productsCreate(body: body));

  Future<void> _put(String url, Uint8List bytes) async {
    try {
      await _uploadDio.put<void>(
        url,
        data: bytes,
        options: Options(
          contentType: 'image/jpeg',
          headers: {Headers.contentLengthHeader: bytes.length},
        ),
      );
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == null) throw const LabelFailure('network');
      if (status == 413) throw const LabelFailure('image_too_large');
      throw const LabelFailure('storage_unavailable');
    }
  }

  static Future<T> _call<T>(Future<T> Function() request) async {
    try {
      return await request();
    } on Object catch (e) {
      throw _failure(e);
    }
  }

  static LabelFailure _failure(Object error) {
    if (error is LabelFailure) return error;
    final code = apiErrorCode(error) ?? 'internal_error';
    final details = error is DioException
        ? parseErrorEnvelope(error.response?.data)?.error.details
        : null;
    final fields = <String>[];
    String? productId;
    if (details is Map) {
      final raw = details['fields'];
      if (raw is List) {
        for (final f in raw.whereType<String>()) {
          final name = f.split('.').last;
          if (name.isNotEmpty && !fields.contains(name)) fields.add(name);
        }
      }
      final id = details['product_id'];
      if (id is String && id.isNotEmpty) productId = id;
    }
    return LabelFailure(code, fields: fields, productId: productId);
  }
}

/// A Dio with no interceptors, only for PUTs to signed storage URLs.
final uploadDioProvider = Provider<Dio>((ref) {
  final dio = Dio();
  ref.onDispose(dio.close);
  return dio;
});

final labelRepositoryProvider = Provider<LabelRepository>((ref) {
  final api = ref.watch(apiClientProvider);
  return LabelRepository(
    scans: api.scans,
    products: api.products,
    uploadDio: ref.watch(uploadDioProvider),
  );
});
