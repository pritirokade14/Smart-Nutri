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
  Future<String?> accessToken() async => _auth.currentSession?.accessToken;

  @override
  Future<void> signInWithGoogle() async {
    // serverClientId is the Web OAuth client that Supabase trusts, so the ID
    // token audience matches.
    _googleInit ??= GoogleSignIn.instance.initialize(
      serverClientId: _config.googleWebClientId,
    );
    await _googleInit;
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
