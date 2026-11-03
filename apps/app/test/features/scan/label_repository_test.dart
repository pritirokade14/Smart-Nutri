import 'dart:math';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';
import 'package:smartnutri_ai/features/scan/data/label_repository.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fixtures.dart';
import 'draft_fixtures.dart';

class _FakeScans implements ScansClient {
  final uploadBodies = <UploadUrlIn>[];
  final labelBodies = <LabelScanIn>[];
  Object? labelError;

  @override
  Future<UploadUrlOut> scansCreateUploadUrl({required UploadUrlIn body}) async {
    uploadBodies.add(body);
    return const UploadUrlOut(
      expiresIn: 600,
      path: 'acc-1/abc.jpg',
      uploadUrl:
          'https://storage.example/upload/sign/labels/acc-1/abc.jpg?token=t',
    );
  }

  @override
  Future<ScanDraftOut> scansCreateLabel({required LabelScanIn body}) async {
    labelBodies.add(body);
    if (labelError case final e?) throw e;
    return scanOut(baseDraft());
  }
}

class _FakeProducts implements ProductsClient {
  _FakeProducts(this.respond);
  final Future<ProductOut> Function() respond;
  final bodies = <ProductCreate>[];

  @override
  Future<ProductOut> productsCreate({required ProductCreate body}) {
    bodies.add(body);
    return respond();
  }

  @override
  Future<ProductOut> productsGetByBarcode({required String code}) =>
      throw UnimplementedError();

  @override
  Future<PublicProductOut> productsGetPublic({
    required String barcode,
    Language? language = Language.en,
  }) => throw UnimplementedError();
}

/// Records every request the upload Dio sends.
class _RecordingAdapter implements HttpClientAdapter {
  _RecordingAdapter([this.status = 200]);
  final int status;
  final requests = <RequestOptions>[];
  final bodies = <List<int>>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final bytes = <int>[];
    if (requestStream != null) {
      await for (final chunk in requestStream) {
        bytes.addAll(chunk);
      }
    }
    bodies.add(bytes);
    return ResponseBody.fromString('{}', status);
  }

  @override
  void close({bool force = false}) {}
}

DioException _apiError(String code, int status, [Object? details]) {
  final ro = RequestOptions(path: '/v1/products');
  return DioException(
    requestOptions: ro,
    response: Response<Object?>(
      requestOptions: ro,
      statusCode: status,
      data: {
        'error': {
          'code': code,
          'message_key': 'error.$code',
          'details': details ?? <String, Object?>{},
        },
      },
    ),
  );
}

ProductCreate _body() => const ProductCreate(
  basis: ProductCreateBasis.per100g,
  category: ProductCreateCategory.general,
  name: 'Marie Biscuit',
  nutrients: PrintedNutrients(
    carbsG: null,
    energyKcal: null,
    fatG: null,
    fiberG: null,
    proteinG: 7.5,
    saltG: null,
    satFatG: null,
    sodiumMg: null,
    sugarsG: null,
  ),
);

void main() {
  test('compressForUpload keeps output ≤ 8 MB', () async {
    // Noise does not compress well, so this is close to the worst case.
    final rnd = Random(7);
    final big = img.Image(width: 3000, height: 2200);
    for (final p in big) {
      p
        ..r = rnd.nextInt(256)
        ..g = rnd.nextInt(256)
        ..b = rnd.nextInt(256);
    }
    final input = img.encodePng(big, level: 0);
    expect(input.length, greaterThan(8 * 1024 * 1024));
    final out = await compressForUpload(input);
    expect(out.length, lessThanOrEqualTo(maxUploadBytes));
    final decoded = img.decodeJpg(out)!;
    expect(max(decoded.width, decoded.height), lessThanOrEqualTo(2000));
  });

  test('compressForUpload rejects bytes that are not an image', () async {
    await expectLater(
      compressForUpload(Uint8List.fromList(List.filled(64, 1))),
      throwsA(
        isA<LabelFailure>().having((f) => f.code, 'code', 'unsupported_image'),
      ),
    );
  });

  test(
    'scanLabel: upload URL, PUT without auth header, then scans_create_label '
    'with the barcode',
    () async {
      final scans = _FakeScans();
      final adapter = _RecordingAdapter();
      final upload = Dio()..httpClientAdapter = adapter;
      final phases = <LabelPhase>[];
      final repo = LabelRepository(
        scans: scans,
        products: _FakeProducts(() async => analyzeFixture('water').product),
        uploadDio: upload,
        compress: (b) async => b,
      );
      final photo = XFile.fromData(
        Uint8List.fromList([1, 2, 3]),
        name: 'a.jpg',
      );
      final out = await repo.scanLabel(
        photo,
        barcode: '8901063201089',
        onPhase: phases.add,
      );
      expect(out.scanId, 'scan-1');
      expect(scans.uploadBodies.single.ext, UploadUrlInExt.jpg);
      final put = adapter.requests.single;
      expect(put.method, 'PUT');
      expect(put.uri.host, 'storage.example');
      expect(
        put.headers.keys.map((k) => k.toLowerCase()),
        isNot(contains('authorization')),
      );
      expect(put.contentType, 'image/jpeg');
      expect(adapter.bodies.single, [1, 2, 3]);
      expect(scans.labelBodies.single.path, 'acc-1/abc.jpg');
      expect(scans.labelBodies.single.barcode, '8901063201089');
      expect(phases, [LabelPhase.uploading, LabelPhase.reading]);
    },
  );

  test('scanLabel maps API error codes', () async {
    final scans = _FakeScans()
      ..labelError = _apiError('extraction_failed', 502);
    final repo = LabelRepository(
      scans: scans,
      products: _FakeProducts(() async => analyzeFixture('water').product),
      uploadDio: Dio()..httpClientAdapter = _RecordingAdapter(),
      compress: (b) async => b,
    );
    await expectLater(
      repo.scanLabel(XFile.fromData(Uint8List.fromList([1]))),
      throwsA(
        isA<LabelFailure>().having((f) => f.code, 'code', 'extraction_failed'),
      ),
    );
  });

  test('a failed PUT is a storage failure (413 is image_too_large)', () async {
    Future<String> codeFor(int status) async {
      final repo = LabelRepository(
        scans: _FakeScans(),
        products: _FakeProducts(() async => analyzeFixture('water').product),
        uploadDio: Dio()..httpClientAdapter = _RecordingAdapter(status),
        compress: (b) async => b,
      );
      try {
        await repo.scanLabel(XFile.fromData(Uint8List.fromList([1])));
      } on LabelFailure catch (f) {
        return f.code;
      }
      return 'none';
    }

    expect(await codeFor(500), 'storage_unavailable');
    expect(await codeFor(413), 'image_too_large');
  });

  test('saveDraft sends the body unchanged and returns the product', () async {
    final product = analyzeFixture('water').product;
    final products = _FakeProducts(() async => product);
    final repo = LabelRepository(
      scans: _FakeScans(),
      products: products,
      uploadDio: Dio(),
    );
    final body = _body();
    expect(await repo.saveDraft(body), same(product));
    expect(products.bodies.single, same(body));
  });

  test(
    'saveDraft maps implausible_value fields and product_exists id',
    () async {
      Future<LabelFailure> failureFor(DioException e) async {
        final repo = LabelRepository(
          scans: _FakeScans(),
          products: _FakeProducts(() async => throw e),
          uploadDio: Dio(),
        );
        try {
          await repo.saveDraft(_body());
        } on LabelFailure catch (f) {
          return f;
        }
        fail('no failure');
      }

      final implausible = await failureFor(
        _apiError('implausible_value', 422, {
          'field': 'protein_g',
          'fields': ['protein_g', 'serving_size_g'],
        }),
      );
      expect(implausible.code, 'implausible_value');
      expect(implausible.fields, ['protein_g', 'serving_size_g']);

      final validation = await failureFor(
        _apiError('validation_error', 422, {
          'fields': ['body.nutrients.sodium_mg', 'body.serving_size_g'],
        }),
      );
      expect(validation.fields, ['sodium_mg', 'serving_size_g']);

      // A list item names the list: the ingredients field is highlighted.
      final ingredient = await failureFor(
        _apiError('validation_error', 422, {
          'fields': ['body.ingredients.3', 'body.ingredients.7', 'body.basis'],
        }),
      );
      expect(ingredient.fields, ['ingredients', 'basis']);

      final exists = await failureFor(
        _apiError('product_exists', 409, {'product_id': 'p-9'}),
      );
      expect(exists.code, 'product_exists');
      expect(exists.productId, 'p-9');
    },
  );
}
