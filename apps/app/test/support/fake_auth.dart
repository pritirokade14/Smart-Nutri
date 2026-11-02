import 'dart:async';

import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';

class FakeAuthRepository implements AuthRepository {
  FakeAuthRepository({bool signedIn = false}) {
    _signedIn = signedIn;
  }

  bool _signedIn = false;
  final _controller = StreamController<bool>.broadcast();
  final calls = <String>[];

  @override
  Stream<bool> authStateChanges() => _controller.stream;

  @override
  bool get isSignedIn => _signedIn;

  @override
  Future<String?> accessToken() async => _signedIn ? 'tok' : null;

  void setSignedIn(bool v) {
    _signedIn = v;
    _controller.add(v);
  }

  @override
  Future<void> signInWithGoogle() async => calls.add('google');

  @override
  Future<void> sendEmailOtp(String email) async =>
      calls.add('sendEmail:$email');

  @override
  Future<void> verifyEmailOtp(String email, String code) async {
    calls.add('verifyEmail:$email:$code');
    setSignedIn(true);
  }

  @override
  Future<void> sendPhoneOtp(String phone) async =>
      calls.add('sendPhone:$phone');

  @override
  Future<void> verifyPhoneOtp(String phone, String code) async {
    calls.add('verifyPhone:$phone:$code');
    setSignedIn(true);
  }

  @override
  Future<void> signOut() async {
    calls.add('signOut');
    setSignedIn(false);
  }
}
