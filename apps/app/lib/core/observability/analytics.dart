import 'dart:async';

import 'package:flutter/foundation.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:posthog_flutter/posthog_flutter.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import '../config/app_config.dart';

/// The only events the app sends, and the properties each may carry. Mirrors
/// `ALLOWED_EVENTS` in `apps/api/app/integrations/posthog.py` exactly (and
/// the web's `analytics.ts`). No health data ever: no conditions, allergens,
/// diets, statuses, reasons, nutrients, names, emails or ids.
const Map<String, Set<String>> allowedEvents = {
  'app_opened': {},
  'scan_started': {'method'},
  'scan_completed': {'method', 'found'},
  'verdicts_shown': {'member_count'},
  'meal_logged': {},
  'meal_queued': {},
  'meal_log_undone': {},
  'meal_removed': {},
  'share_result': {},
  'share_weekly': {},
  'compare_opened': {},
  'compare_viewed': {},
  'product_search': {},
  'diary_entry_added': {'method'},
  'diary_day_viewed': {},
  'voice_asked': {'language'},
  'report_submitted': {'reason'},
  'share_clicked': {'kind'},
  'account_deleted': {},
};

/// Properties whose values come from a closed set (as the API's `_ENUMS`).
const Map<String, Set<String>> _enums = {
  'method': {
    'barcode',
    'label',
    'manual',
    'search',
    'recent',
    'favourite',
    'quick_add',
    'custom',
    'recipe',
    'copy',
  },
  'language': {'en', 'hi', 'mr'},
  'reason': {'wrong_values', 'wrong_ingredients', 'wrong_product', 'other'},
  'kind': {'link', 'image', 'whatsapp'},
};
const Set<String> _bools = {'found'};
const Set<String> _counts = {'member_count'};

/// Hard-coded PostHog ingest host (US cloud); no config key by design.
const String posthogHost = 'https://us.i.posthog.com';

typedef AnalyticsSink =
    Future<void> Function(String event, Map<String, Object> props);

final RegExp _token = RegExp(r'^[a-z0-9_]{1,40}$');

bool _validValue(String key, Object value) {
  if (_bools.contains(key)) return value is bool;
  if (_counts.contains(key)) return value is int && value >= 0 && value <= 1000;
  if (value is! String || !_token.hasMatch(value)) return false;
  return _enums[key]?.contains(value) ?? true;
}

/// The allow-listed, safely valued properties of [event]; empty for an
/// event outside [allowedEvents].
Map<String, Object> filterProps(String event, Map<String, Object?>? props) {
  final allowed = allowedEvents[event] ?? const <String>{};
  return {
    for (final e in (props ?? const <String, Object?>{}).entries)
      if (allowed.contains(e.key) &&
          e.value != null &&
          _validValue(e.key, e.value!))
        e.key: e.value!,
  };
}

class Analytics {
  const Analytics(AnalyticsSink this._sink);

  /// No-op: used without a PostHog key and in tests.
  const Analytics.disabled() : _sink = null;

  final AnalyticsSink? _sink;

  /// Sends [event] with its allow-listed [props]. An event outside
  /// [allowedEvents] is dropped, with a debug-only warning that names it
  /// (values are never logged).
  Future<void> track(String event, [Map<String, Object?>? props]) async {
    if (!allowedEvents.containsKey(event)) {
      assert(() {
        debugPrint('analytics: dropped unknown event "$event"');
        return true;
      }());
      return;
    }
    final kept = filterProps(event, props);
    assert(() {
      final dropped = (props?.keys ?? const <String>[]).where(
        (k) => !kept.containsKey(k),
      );
      if (dropped.isNotEmpty) {
        debugPrint('analytics: dropped props ${dropped.join(',')} on $event');
      }
      return true;
    }());
    final sink = _sink;
    if (sink == null) return;
    await sink(event, kept);
  }
}

/// Sentry beforeSend: drop request data, cookies and headers; keep only user id.
SentryEvent? scrubSentryEvent(SentryEvent event, Hint hint) {
  event.request = null;
  // Exception text (e.g. DioException URIs with query strings) can hold health data.
  for (final ex in event.exceptions ?? const <SentryException>[]) {
    ex.value = '<redacted>';
  }
  event.breadcrumbs = null;
  // FlutterErrorIntegration attaches widget diagnostics, which can include
  // user-entered text; free-form message/extra may too.
  event.contexts.remove('flutter_error_details');
  event.message = null;
  // ignore: deprecated_member_use
  event.extra = null;
  final user = event.user;
  if (user != null) {
    event.user = user.id == null ? null : SentryUser(id: user.id);
  }
  return event;
}

/// Analytics for features; a no-op until bootstrap overrides it with the real one.
final analyticsProvider = Provider<Analytics>(
  (ref) => const Analytics.disabled(),
);

/// Sets up PostHog when a key is configured; otherwise returns a no-op.
Future<Analytics> initAnalytics(AppConfig config) async {
  if (config.posthogKey.isEmpty) return const Analytics.disabled();
  final c = PostHogConfig(config.posthogKey)
    ..host = posthogHost
    ..personProfiles = PostHogPersonProfiles.identifiedOnly
    ..captureApplicationLifecycleEvents = false
    ..sessionReplay = false
    ..surveys = false
    ..preloadFeatureFlags = false
    ..sendFeatureFlagEvent = false
    ..debug = false;
  await Posthog().setup(c);
  return Analytics(
    (event, props) => Posthog().capture(
      eventName: event,
      properties: {'platform': 'android', r'$geoip_disable': true, ...props},
    ),
  );
}

/// Runs [appRunner] under Sentry when a DSN is configured, else directly.
Future<void> runWithSentry(
  AppConfig config,
  FutureOr<void> Function() appRunner,
) async {
  if (config.sentryDsn.isEmpty) {
    await appRunner();
    return;
  }
  await SentryFlutter.init((o) {
    o.dsn = config.sentryDsn;
    o.environment = config.environment;
    o.sendDefaultPii = false;
    o.attachScreenshot = false;
    o.tracesSampleRate = config.environment == 'prod' ? 0.1 : 0;
    o.beforeSend = scrubSentryEvent;
    o.maxBreadcrumbs = 0;
  }, appRunner: appRunner);
}
