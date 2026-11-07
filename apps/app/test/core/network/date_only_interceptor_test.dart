import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/network/date_only_interceptor.dart';
import 'package:smartnutri_ai/features/diary/domain/diary_dates.dart';
import 'package:smartnutri_api/src/export.dart';

class _Capture extends Interceptor {
  RequestOptions? last;
  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    last = o;
    h.resolve(Response(requestOptions: o, data: <String, Object?>{}));
  }
}

void main() {
  late _Capture cap;
  late SmartNutriApiClient client;
  setUp(() {
    cap = _Capture();
    final dio = Dio(BaseOptions(baseUrl: 'http://x'))
      ..interceptors.addAll([DateOnlyInterceptor(), cap]);
    client = SmartNutriApiClient(dio);
  });

  test('day and week query dates are plain YYYY-MM-DD', () async {
    try {
      await client.diary.diaryDayGet(date: parseDateKey('2026-11-06'));
    } on Object {
      // empty fake body
    }
    expect(cap.last!.queryParameters['date'], '2026-11-06');
    try {
      await client.diary.diaryWeekGet(end: parseDateKey('2026-11-06'));
    } on Object {
      // empty fake body
    }
    expect(cap.last!.queryParameters['end'], '2026-11-06');
  });

  test('status path day is plain', () async {
    try {
      await client.diary.diaryDayStatusPut(
        day: parseDateKey('2026-11-06')!,
        body: DiaryDayStatusIn(partialLogged: true),
      );
    } on Object {
      // empty fake body
    }
    expect(cap.last!.path, '/v1/diary/days/2026-11-06/status');
  });

  test('copy body dates are plain', () async {
    try {
      await client.meals.mealsCopy(
        body: CopyIn(
          fromDate: parseDateKey('2026-11-05')!,
          toDate: parseDateKey('2026-11-06')!,
          clientId: 'c',
        ),
      );
    } on Object {
      // empty fake body
    }
    final d = cap.last!.data as Map;
    expect(d['from_date'], '2026-11-05');
    expect(d['to_date'], '2026-11-06');
  });
}
