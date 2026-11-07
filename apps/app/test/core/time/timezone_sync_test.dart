import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/time/timezone_sync.dart';
import 'package:smartnutri_api/src/export.dart';

import '../../support/fake_meals.dart';
import '../../support/fake_user_types.dart';

class _Me extends FakeUserTypesMe {
  final zones = <String>[];
  Object? putError;

  @override
  Future<MeOut> meTimezonePut({required TimezoneIn body}) async {
    zones.add(body.timezone);
    if (putError case final e?) throw e;
    return meGet();
  }
}

void main() {
  test('sends zone only when it differs', () async {
    final c = _Me();
    final me = await c.meGet(); // timezone: Asia/Kolkata
    await syncTimezone(me, c, localZone: () async => 'Asia/Kolkata');
    expect(c.zones, isEmpty);
    await syncTimezone(me, c, localZone: () async => 'America/New_York');
    expect(c.zones, ['America/New_York']);
  });

  test('plugin failure sends nothing', () async {
    final c = _Me();
    final me = await c.meGet();
    await syncTimezone(
      me,
      c,
      localZone: () async => throw StateError('no plugin'),
    );
    await syncTimezone(me, c, localZone: () async => '');
    expect(c.zones, isEmpty);
  });

  test('an API refusal is ignored', () async {
    final c = _Me()..putError = apiError(422, 'timezone_invalid');
    final me = await c.meGet();
    await syncTimezone(me, c, localZone: () async => 'Mars/Base');
    expect(c.zones, ['Mars/Base']);
  });
}
