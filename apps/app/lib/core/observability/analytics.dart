import 'dart:async';

import 'package:posthog_flutter/posthog_flutter.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import '../config/app_config.dart';

/// Same allow-list as the API (observability.py) and web (lib/analytics.ts).
/// No health data (conditions, allergies, diets, verdicts, names) ever.
const Set<String> allowedEventProps = {
  'platform',
  'locale',
  'screen',
  'status_code',
  'source',
};

/// Hard-coded PostHog ingest host (US cloud); no config key by design.
const String posthogHost = 'https://us.i.posthog.com';

typedef AnalyticsSink =
    Future<void> Function(String event, Map<String, Object> props);

Map<String, Object> filterProps(Map<String, Object?>? props) => {
  for (final e in (props ?? const <String, Object?>{}).entries)
    if (allowedEventProps.contains(e.key) && e.value != null) e.key: e.value!,
};

class Analytics {
  const Analytics(AnalyticsSink this._sink);

  /// No-op: used without a PostHog key and in tests.
  const Analytics.disabled() : _sink = null;

  final AnalyticsSink? _sink;

  Future<void> track(String event, [Map<String, Object?>? props]) async {
    final sink = _sink;
    if (sink == null) return;
    await sink(event, filterProps(props));
  }
}

/// Sentry beforeSend: drop request data, cookies and headers; keep only user id.
SentryEvent? scrubSentryEvent(SentryEvent event, Hint hint) {
  event.request = null;
  final user = event.user;
  if (user != null) {
    event.user = user.id == null ? null : SentryUser(id: user.id);
  }
  return event;
}

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
      properties: {'platform': 'android', ...props},
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
