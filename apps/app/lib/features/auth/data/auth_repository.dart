import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/config/app_config.dart';

abstract interface class AuthRepository {
  Stream<bool> authStateChanges();
  bool get isSignedIn;
  Future<String?> accessToken();
  Future<void> signInWithGoogle();
  Future<void> sendEmailOtp(String email);
  Future<void> verifyEmailOtp(String email, String code);
  Future<void> sendPhoneOtp(String phone);
  Future<void> verifyPhoneOtp(String phone, String code);
  Future<void> signOut();
}

/// Returns [token] unless it is missing or [expired]; an expired token is
/// refreshed. A transient failure (network, 5xx) is rethrown so the request
/// fails without a token and the session is kept. Null is returned only for a
/// non-retryable auth failure (e.g. invalid refresh token).
Future<String?> freshAccessToken({
  required String? token,
  required bool expired,
  required Future<String?> Function() refresh,
}) async {
  if (token == null) return null;
  if (!expired) return token;
  try {
    return await refresh();
  } on AuthRetryableFetchException {
    rethrow;
  } on AuthException {
    return null;
  }
}

class SupabaseAuthRepository implements AuthRepository {
  SupabaseAuthRepository(this._config);

  final AppConfig _config;
  Future<void>? _googleInit;

  GoTrueClient get _auth => Supabase.instance.client.auth;

  @override
  Stream<bool> authStateChanges() =>
      _auth.onAuthStateChange.map((s) => s.session != null);

  @override
  bool get isSignedIn => _auth.currentSession != null;

  @override
  Future<String?> accessToken() {
    final s = _auth.currentSession;
    return freshAccessToken(
      token: s?.accessToken,
      expired: s?.isExpired ?? false,
      refresh: () async => (await _auth.refreshSession()).session?.accessToken,
    );
  }

  @override
  Future<void> signInWithGoogle() async {
    // serverClientId is the Web OAuth client that Supabase trusts, so the ID
    // token audience matches.
    _googleInit ??= GoogleSignIn.instance.initialize(
      serverClientId: _config.googleWebClientId,
    );
    try {
      await _googleInit;
    } catch (_) {
      _googleInit = null; // allow a retry
      rethrow;
    }
    final account = await GoogleSignIn.instance.authenticate();
    final idToken = account.authentication.idToken;
    if (idToken == null) {
      throw const AuthException('Google did not return an ID token');
    }
    await _auth.signInWithIdToken(
      provider: OAuthProvider.google,
      idToken: idToken,
    );
  }

  @override
  Future<void> sendEmailOtp(String email) => _auth.signInWithOtp(email: email);

  @override
  Future<void> verifyEmailOtp(String email, String code) =>
      _auth.verifyOTP(email: email, token: code, type: OtpType.email);

  @override
  Future<void> sendPhoneOtp(String phone) => _auth.signInWithOtp(phone: phone);

  @override
  Future<void> verifyPhoneOtp(String phone, String code) =>
      _auth.verifyOTP(phone: phone, token: code, type: OtpType.sms);

  @override
  Future<void> signOut() => _auth.signOut();
}

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => SupabaseAuthRepository(ref.watch(appConfigProvider)),
);

/// Whether a session exists, updated on every sign-in and sign-out. The API
/// client watches it, so every account-scoped provider (members, consents,
/// results, ...) is rebuilt and its cached data dropped when the account
/// changes or signs out.
class SignedInNotifier extends Notifier<bool> {
  @override
  bool build() {
    final auth = ref.watch(authRepositoryProvider);
    final sub = auth.authStateChanges().listen((v) => state = v);
    ref.onDispose(sub.cancel);
    return auth.isSignedIn;
  }
}

final signedInProvider = NotifierProvider<SignedInNotifier, bool>(
  SignedInNotifier.new,
);
