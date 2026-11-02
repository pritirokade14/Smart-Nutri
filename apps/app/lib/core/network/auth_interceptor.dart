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
    final String? token;
    try {
      token = await _token();
    } catch (e) {
      // Never leave the request hanging; fail it without signing the user out.
      handler.reject(
        DioException(
          requestOptions: options,
          type: DioExceptionType.unknown,
          error: e,
        ),
      );
      return;
    }
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
    // Only a rejected token counts; a request sent without one says nothing
    // about the session.
    final sentToken = err.requestOptions.headers.containsKey('Authorization');
    if (sentToken && err.response?.statusCode == 401) {
      try {
        await _onUnauthorized();
      } catch (_) {
        // The original error must still reach the caller.
      }
    }
    handler.next(err);
  }
}
