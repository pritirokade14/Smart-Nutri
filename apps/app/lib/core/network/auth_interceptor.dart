import 'package:dio/dio.dart';

/// Adds the Supabase access token and reports 401s. It never retries, so a
/// rejected token cannot cause a request loop.
class AuthInterceptor extends Interceptor {
  AuthInterceptor(this._token, this._onUnauthorized);

  final Future<String?> Function() _token;
  final Future<void> Function() _onUnauthorized;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _token();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      await _onUnauthorized();
    }
    handler.next(err);
  }
}
