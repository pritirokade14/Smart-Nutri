import 'package:dio/dio.dart';

import '../domain/consent_error.dart';

/// Reports every 403 `consent_required` to [onRequired] with the purposes it
/// names, so the app can open the matching consent screen. The error still
/// reaches the caller, which shows its own error state.
///
/// Member saves are left out: the member form opens the health-data consent
/// sheet itself and retries the save.
class ConsentRequiredInterceptor extends Interceptor {
  ConsentRequiredInterceptor(this._onRequired);

  final void Function(List<String> purposes) _onRequired;

  static bool _handledInPlace(String path) => path.contains('/v1/members');

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
