import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:smartnutri_ai/core/config/app_config.dart';

/// A stand-in for a configured `SITE_URL` (never a real, hard-coded domain).
const testSiteUrl = 'https://site.example';

/// An [AppConfig] for widget tests; [siteUrl] empty means no `SITE_URL`.
AppConfig testConfig({String siteUrl = testSiteUrl}) => AppConfig(
  environment: 'test',
  apiBaseUrl: 'http://api.test',
  supabaseUrl: 'http://supabase.test',
  supabasePublishableKey: 'k',
  googleWebClientId: '',
  sentryDsn: '',
  posthogKey: '',
  featurePhoneOtp: false,
  siteUrl: siteUrl,
);

/// Overrides [appConfigProvider] with [testConfig].
Override testConfigOverride({String siteUrl = testSiteUrl}) =>
    appConfigProvider.overrideWithValue(testConfig(siteUrl: siteUrl));
