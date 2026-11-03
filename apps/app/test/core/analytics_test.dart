import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'package:smartnutri_ai/core/observability/analytics.dart';

void main() {
  test('allowed events mirror the API ALLOWED_EVENTS exactly', () {
    // apps/api/app/integrations/posthog.py::ALLOWED_EVENTS
    expect(allowedEvents, {
      'app_opened': <String>{},
      'scan_started': {'method'},
      'scan_completed': {'method', 'found'},
      'verdicts_shown': {'member_count'},
      'meal_logged': <String>{},
      'voice_asked': {'language'},
      'report_submitted': {'reason'},
      'share_clicked': {'kind'},
      'account_deleted': <String>{},
    });
  });

  test('track_drops_unknown_props', () async {
    final sent = <(String, Map<String, Object>)>[];
    final a = Analytics((e, p) async => sent.add((e, p)));
    await a.track('scan_completed', {
      'method': 'barcode',
      'found': true,
      'reason': 'allergen_contains',
      'conditions': ['diabetes'],
      'screen': 'home',
    });
    expect(sent.single.$1, 'scan_completed');
    expect(sent.single.$2, {'method': 'barcode', 'found': true});
  });

  test('track ignores events outside the allow-list', () async {
    final sent = <String>[];
    final a = Analytics((e, p) async => sent.add(e));
    await a.track('viewed', {'screen': 'home'});
    await a.track('label_scan_failed');
    expect(sent, isEmpty);
  });

  test('track is a no-op without a sink (no key)', () async {
    await const Analytics.disabled().track('app_opened');
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

  test('scrubSentryEvent drops flutter error details, message and extra', () {
    final event = SentryEvent(
      message: SentryMessage('member Asha has diabetes'),
      // ignore: deprecated_member_use
      extra: {'allergies': 'peanut'},
    );
    event.contexts['flutter_error_details'] = {
      'information': 'TextField(controller: "Asha")',
    };
    event.contexts['os'] = {'name': 'Android'};
    final out = scrubSentryEvent(event, Hint())!;
    expect(out.contexts.containsKey('flutter_error_details'), isFalse);
    expect(out.contexts.containsKey('os'), isTrue);
    expect(out.message, isNull);
    // ignore: deprecated_member_use
    expect(out.extra, isNull);
  });

  test('track constrains allow-listed values', () async {
    final sent = <Map<String, Object>>[];
    final a = Analytics((e, p) async => sent.add(p));
    await a.track('scan_started', {'method': 'photo'});
    expect(sent.last, isEmpty);
    await a.track('scan_completed', {'method': 'label', 'found': 'yes'});
    expect(sent.last, {'method': 'label'});
    await a.track('verdicts_shown', {'member_count': true});
    expect(sent.last, isEmpty);
    await a.track('verdicts_shown', {'member_count': 4});
    expect(sent.last, {'member_count': 4});
    await a.track('verdicts_shown', {'member_count': 5000});
    expect(sent.last, isEmpty);
    await a.track('voice_asked', {'language': 'fr'});
    expect(sent.last, isEmpty);
    await a.track('voice_asked', {'language': 'mr'});
    expect(sent.last, {'language': 'mr'});
    await a.track('report_submitted', {'reason': 'wrong_values'});
    expect(sent.last, {'reason': 'wrong_values'});
    await a.track('report_submitted', {'reason': 'Has peanuts'});
    expect(sent.last, isEmpty);
    await a.track('share_clicked', {'kind': 'whatsapp'});
    expect(sent.last, {'kind': 'whatsapp'});
  });

  test('analyticsProvider defaults to a no-op and can be overridden', () async {
    final c = ProviderContainer();
    addTearDown(c.dispose);
    await c.read(analyticsProvider).track('app_opened');
    final sent = <String>[];
    final c2 = ProviderContainer(
      overrides: [
        analyticsProvider.overrideWithValue(
          Analytics((e, p) async => sent.add(e)),
        ),
      ],
    );
    addTearDown(c2.dispose);
    await c2.read(analyticsProvider).track('app_opened');
    expect(sent, ['app_opened']);
  });
}
