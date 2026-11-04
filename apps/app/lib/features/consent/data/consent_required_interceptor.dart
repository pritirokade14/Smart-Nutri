import 'package:dio/dio.dart';

import '../domain/consent_error.dart';

/// Reports every 403 `consent_required` to [onRequired] with the purposes it
/// names, so the app can open the matching consent screen. The error still
/// reaches the caller, which shows its own error state.
///
/// Member saves and user-type saves are left out: those screens open the
/// health-data consent sheet themselves and retry the save.
class ConsentRequiredInterceptor extends Interceptor {
  ConsentRequiredInterceptor(this._onRequired);

  final void Function(List<String> purposes) _onRequired;

  static bool _handledInPlace(String path) =>
      path.contains('/v1/members') || path.contains('/v1/me/user-types');

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final purposes = consentPurposesOf(err);
    if (purposes != null &&
        purposes.isNotEmpty &&
        !_handledInPlace(err.requestOptions.path)) {
      _onRequired(purposes);
    }
    handler.next(err);
  }
}
