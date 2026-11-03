import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/config/app_config.dart';

void main() {
  test('missingRequired lists empty required keys', () {
    const c = AppConfig(
      environment: 'dev',
      apiBaseUrl: '',
      supabaseUrl: 'x',
      supabasePublishableKey: '',
      googleWebClientId: '',
      sentryDsn: '',
      posthogKey: '',
      featurePhoneOtp: false,
    );
    expect(c.missingRequired(), ['API_BASE_URL', 'SUPABASE_PUBLISHABLE_KEY']);
  });

  test('policyUri builds the localized web page, or null without SITE_URL', () {
    const base = AppConfig(
      environment: 'dev',
      apiBaseUrl: 'a',
      supabaseUrl: 'x',
      supabasePublishableKey: 'k',
      googleWebClientId: '',
      sentryDsn: '',
      posthogKey: '',
      featurePhoneOtp: false,
    );
    expect(base.policyUri('privacy', 'en'), isNull);
    const site = AppConfig(
      environment: 'dev',
      apiBaseUrl: 'a',
      supabaseUrl: 'x',
      supabasePublishableKey: 'k',
      googleWebClientId: '',
      sentryDsn: '',
      posthogKey: '',
      featurePhoneOtp: false,
      siteUrl: 'https://smartnutri.in/',
    );
    expect(
      site.policyUri('terms', 'hi').toString(),
      'https://smartnutri.in/hi/terms',
    );
  });
}
