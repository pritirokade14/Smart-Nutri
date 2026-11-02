import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';

void main() {
  test('allow-list matches API and web', () {
    expect(allowedEventProps, {
      'platform',
      'locale',
      'screen',
      'status_code',
      'source',
    });
  });

  test('track drops non-allowed keys and keeps allowed ones', () async {
    final sent = <(String, Map<String, Object>)>[];
    final a = Analytics((e, p) async => sent.add((e, p)));
    await a.track('viewed', {
      'conditions': ['diabetes'],
      'screen': 'home',
    });
    expect(sent.single.$1, 'viewed');
    expect(sent.single.$2, {'screen': 'home'});
  });

  test('track is a no-op without a sink (no key)', () async {
    await const Analytics.disabled().track('viewed', {'screen': 'home'});
  });

  test('scrubSentryEvent removes body, cookies, headers, email and ip', () {
    final event = SentryEvent(
      request: SentryRequest(
        url: 'https://x.in/a?next=1',
        data: {'allergy': 'peanut'},
        cookies: 's=1',
        headers: {'Authorization': 'Bearer x'},
        queryString: 'next=1',
      ),
      user: SentryUser(id: 'u', email: 'a@b.c', ipAddress: '1.1.1.1'),
    );
    final out = scrubSentryEvent(event, Hint())!;
    expect(out.request, isNull);
    expect(out.user?.id, 'u');
    expect(out.user?.email, isNull);
    expect(out.user?.ipAddress, isNull);
  });

  test('scrubSentryEvent redacts exception text and breadcrumbs', () {
    final event = SentryEvent(
      exceptions: [
        SentryException(
          type: 'DioException',
          value: 'GET https://api/x?conditions=diabetes failed',
          module: 'dio',
        ),
      ],
      breadcrumbs: [Breadcrumb(message: 'diabetes')],
    );
    final out = scrubSentryEvent(event, Hint())!;
    expect(out.exceptions!.single.value, '<redacted>');
    expect(out.exceptions!.single.type, 'DioException');
    expect(out.breadcrumbs, isNull);
  });

  test('track constrains allow-listed values', () async {
    final sent = <Map<String, Object>>[];
    final a = Analytics((e, p) async => sent.add(p));
    await a.track('e', {
      'locale': 'fr',
      'platform': 'ios',
      'screen': 'Diabetes Home',
      'source': 'scan_page',
      'status_code': '200',
    });
    expect(sent.last, {'source': 'scan_page'});
    await a.track('e', {
      'locale': 'mr',
      'platform': 'android',
      'screen': 'home',
      'status_code': 404,
    });
    expect(sent.last, {
      'locale': 'mr',
      'platform': 'android',
      'screen': 'home',
      'status_code': 404,
    });
  });

  test('analyticsProvider defaults to a no-op and can be overridden', () async {
    final c = ProviderContainer();
    addTearDown(c.dispose);
    await c.read(analyticsProvider).track('e', {'screen': 'home'});
    final sent = <String>[];
    final c2 = ProviderContainer(
      overrides: [
        analyticsProvider.overrideWithValue(
          Analytics((e, p) async => sent.add(e)),
        ),
      ],
    );
    addTearDown(c2.dispose);
    await c2.read(analyticsProvider).track('hit');
    expect(sent, ['hit']);
  });
}
