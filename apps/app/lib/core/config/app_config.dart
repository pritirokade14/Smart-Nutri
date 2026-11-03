import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Public build-time configuration from `--dart-define-from-file`.
/// No secrets belong here.
class AppConfig {
  const AppConfig({
    required this.environment,
    required this.apiBaseUrl,
    required this.supabaseUrl,
    required this.supabasePublishableKey,
    required this.googleWebClientId,
    required this.sentryDsn,
    required this.posthogKey,
    required this.featurePhoneOtp,
    this.featureEmailOtp = false,
  });

  const AppConfig.fromEnvironment()
    : environment = const String.fromEnvironment(
        'ENVIRONMENT',
        defaultValue: 'dev',
      ),
      apiBaseUrl = const String.fromEnvironment('API_BASE_URL'),
      supabaseUrl = const String.fromEnvironment('SUPABASE_URL'),
      supabasePublishableKey = const String.fromEnvironment(
        'SUPABASE_PUBLISHABLE_KEY',
      ),
      googleWebClientId = const String.fromEnvironment('GOOGLE_WEB_CLIENT_ID'),
      sentryDsn = const String.fromEnvironment('SENTRY_DSN'),
      posthogKey = const String.fromEnvironment('POSTHOG_KEY'),
      featurePhoneOtp = const bool.fromEnvironment('FEATURE_PHONE_OTP'),
      featureEmailOtp = const bool.fromEnvironment(
        'FEATURE_EMAIL_OTP',
        defaultValue: false,
      );

  final String environment;
  final String apiBaseUrl;
  final String supabaseUrl;
  final String supabasePublishableKey;
  final String googleWebClientId;
  final String sentryDsn;
  final String posthogKey;
  final bool featurePhoneOtp;
  final bool featureEmailOtp;

  /// Names of required keys that are empty.
  List<String> missingRequired() => [
    if (apiBaseUrl.isEmpty) 'API_BASE_URL',
    if (supabaseUrl.isEmpty) 'SUPABASE_URL',
    if (supabasePublishableKey.isEmpty) 'SUPABASE_PUBLISHABLE_KEY',
  ];
}

final appConfigProvider = Provider<AppConfig>(
  (ref) => const AppConfig.fromEnvironment(),
);
