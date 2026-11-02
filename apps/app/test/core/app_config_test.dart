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
}
