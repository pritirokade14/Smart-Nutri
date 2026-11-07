import 'package:smartnutri_api/src/export.dart';

import 'fixtures.dart';

/// `WeightsClient` over the golden weight files. Records every call.
class FakeWeightsClient implements WeightsClient {
  FakeWeightsClient({String trend = 'weekly_rate_loss', WeightsOut? list})
    : trend = weightTrendFixture(trend),
      list = list ?? weightsListFixture(trend);

  WeightTrendOut trend;
  WeightsOut list;

  /// Thrown by the next calls, in order (null entries: no error).
  final putErrors = <Object>[];
  Object? trendError;
  Object? listError;
  Object? deleteError;

  final puts = <(DateTime, WeightIn)>[];
  final deletes = <DateTime>[];
  final trendDays = <Days?>[];

  @override
  Future<WeightsOut> weightsList({
    String? memberId,
    DateTime? from,
    DateTime? to,
  }) async {
    if (listError case final e?) throw e;
    return list;
  }

  @override
  Future<WeightTrendOut> weightsTrendGet({
    Days? days = Days.value90,
    String? memberId,
  }) async {
    trendDays.add(days);
    if (trendError case final e?) throw e;
    return trend;
  }

  @override
  Future<void> weightsDelete({required DateTime day, String? memberId}) async {
    if (deleteError case final e?) throw e;
    deletes.add(day);
  }

  var deleteAllCalls = 0;

  @override
  Future<WeightsDeletedOut> weightsDeleteAll({String? memberId}) async {
    if (deleteError case final e?) throw e;
    deleteAllCalls++;
    final n = list.items.length;
    return WeightsDeletedOut(deleted: n);
  }

  @override
  Future<WeightOut> weightsPut({
    required DateTime day,
    required WeightIn body,
  }) async {
    puts.add((day, body));
    if (putErrors.isNotEmpty) throw putErrors.removeAt(0);
    return WeightOut(
      clientId: body.clientId,
      date: day,
      measuredAt: DateTime.utc(2026, 11, 7, 7),
      numbersHidden: false,
      source: 'manual',
      weightKg: body.weightKg,
    );
  }
}
