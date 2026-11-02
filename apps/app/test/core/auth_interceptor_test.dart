import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/network/auth_interceptor.dart';

class _Adapter implements HttpClientAdapter {
  _Adapter(this.status);
  final int status;
  final seen = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    seen.add(options);
    return ResponseBody.fromString(
      jsonEncode({'ok': true}),
      status,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  test('adds bearer token', () async {
    final adapter = _Adapter(200);
    final dio = Dio(BaseOptions(baseUrl: 'http://x'))
      ..httpClientAdapter = adapter
      ..interceptors.add(AuthInterceptor(() async => 't1', () async {}));
    await dio.get<Object?>('/v1/me');
    expect(adapter.seen.single.headers['Authorization'], 'Bearer t1');
  });

  test('no header when there is no token', () async {
    final adapter = _Adapter(200);
    final dio = Dio(BaseOptions(baseUrl: 'http://x'))
      ..httpClientAdapter = adapter
      ..interceptors.add(AuthInterceptor(() async => null, () async {}));
    await dio.get<Object?>('/v1/me');
    expect(adapter.seen.single.headers.containsKey('Authorization'), isFalse);
  });

  test('401 triggers onUnauthorized once and does not retry', () async {
    final adapter = _Adapter(401);
    var calls = 0;
    final dio = Dio(BaseOptions(baseUrl: 'http://x'))
      ..httpClientAdapter = adapter
      ..interceptors.add(
        AuthInterceptor(() async => 't1', () async => calls++),
      );
    await expectLater(dio.get<Object?>('/v1/me'), throwsA(isA<DioException>()));
    expect(calls, 1);
    expect(adapter.seen.length, 1);
  });

  test('a throwing onUnauthorized still surfaces the original error', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://x'))
      ..httpClientAdapter = _Adapter(401)
      ..interceptors.add(
        AuthInterceptor(() async => 't1', () async => throw StateError('x')),
      );
    await expectLater(
      dio.get<Object?>('/v1/me'),
      throwsA(
        isA<DioException>().having(
          (e) => e.response?.statusCode,
          'status',
          401,
        ),
      ),
    );
  });
}
