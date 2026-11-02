import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

void main() {
  Future<String?> never() async => fail('refresh should not be called');

  test('null session gives null', () async {
    expect(
      await freshAccessToken(token: null, expired: false, refresh: never),
      isNull,
    );
  });

  test('valid token is returned as is', () async {
    expect(
      await freshAccessToken(token: 't', expired: false, refresh: never),
      't',
    );
  });

  test('expired token is refreshed', () async {
    expect(
      await freshAccessToken(
        token: 'old',
        expired: true,
        refresh: () async => 'new',
      ),
      'new',
    );
  });

  test('refresh failure gives null', () async {
    expect(
      await freshAccessToken(
        token: 'old',
        expired: true,
        refresh: () async => throw const AuthException('bad'),
      ),
      isNull,
    );
  });
}
