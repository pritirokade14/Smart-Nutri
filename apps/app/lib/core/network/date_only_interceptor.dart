import 'package:dio/dio.dart';

/// The generated client writes a calendar date as a UTC-midnight date-time
/// (`2026-11-07T00:00:00.000Z`, or `2026-11-07 00:00:00.000Z` in a path).
/// The API wants the plain date (`2026-11-07`) of the account's local day, so
/// this rewrites those values before the request leaves the phone. It never
/// converts a zone: the calendar date in the text is kept as is.
class DateOnlyInterceptor extends Interceptor {
  static final _midnight = RegExp(
    r'(\d{4}-\d{2}-\d{2})[T ]00:00:00(?:\.0+)?Z?',
  );
  static final _exact = RegExp(r'^(\d{4}-\d{2}-\d{2})[T ]00:00:00(?:\.0+)?Z?$');

  static const _dateKeys = {
    'date',
    'end',
    'local_date',
    'from_date',
    'to_date',
  };

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.queryParameters = {
      for (final e in options.queryParameters.entries)
        e.key: _dateKeys.contains(e.key) ? _plain(e.value) : e.value,
    };
    final data = options.data;
    if (data is Map) {
      options.data = {
        for (final e in data.entries)
          e.key: _dateKeys.contains(e.key) ? _plain(e.value) : e.value,
      };
    }
    options.path = options.path.replaceAllMapped(
      RegExp('/diary/days/${_midnight.pattern}/'),
      (m) => '/diary/days/${m.group(1)}/',
    );
    handler.next(options);
  }

  static Object? _plain(Object? v) {
    if (v is String) return _exact.firstMatch(v)?.group(1) ?? v;
    return v;
  }
}
