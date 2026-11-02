import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/core/l10n/app_localizations.dart';
import 'package:smartnutri_ai/features/auth/data/auth_repository.dart';
import 'package:smartnutri_ai/features/auth/presentation/email_otp_screen.dart';

import '../../support/fake_auth.dart';

class _FailingAuth extends FakeAuthRepository {
  @override
  Future<void> sendEmailOtp(String email) async => throw Exception('boom');
}

Widget _host(FakeAuthRepository repo) => ProviderScope(
  overrides: [authRepositoryProvider.overrideWithValue(repo)],
  child: const MaterialApp(
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: EmailOtpScreen(),
  ),
);

bool _enabled(WidgetTester t, String label) =>
    t
        .widget<FilledButton>(find.widgetWithText(FilledButton, label))
        .onPressed !=
    null;

void main() {
  testWidgets('validates, sends, verifies, and can change the email', (
    tester,
  ) async {
    final repo = FakeAuthRepository();
    await tester.pumpWidget(_host(repo));
    final l10n = AppLocalizations.of(
      tester.element(find.byType(EmailOtpScreen)),
    );

    expect(_enabled(tester, l10n.authSendCode), isFalse);
    await tester.enterText(find.byType(TextField), 'nope');
    await tester.pump();
    expect(_enabled(tester, l10n.authSendCode), isFalse);
    await tester.enterText(find.byType(TextField), 'a@b.c');
    await tester.pump();
    expect(_enabled(tester, l10n.authSendCode), isTrue);
    await tester.tap(find.text(l10n.authSendCode));
    await tester.pumpAndSettle();
    expect(repo.calls, ['sendEmail:a@b.c']);

    // Change resets to the email step.
    await tester.tap(find.text(l10n.authChange));
    await tester.pump();
    expect(find.text(l10n.authSendCode), findsOneWidget);
    await tester.tap(find.text(l10n.authSendCode));
    await tester.pumpAndSettle();

    final code = find.widgetWithText(TextField, l10n.authCodeLabel);
    await tester.enterText(code, '12ab34567');
    await tester.pump();
    // digits only, max 6: "123456"
    expect(tester.widget<TextField>(code).controller!.text, '123456');
    await tester.enterText(code, '123');
    await tester.pump();
    expect(_enabled(tester, l10n.authVerify), isFalse);
    await tester.enterText(code, '123456');
    await tester.pump();
    expect(_enabled(tester, l10n.authVerify), isTrue);
    await tester.tap(find.text(l10n.authVerify));
    await tester.pumpAndSettle();
    expect(repo.calls.last, 'verifyEmail:a@b.c:123456');
  });

  testWidgets('send failure shows the localized error', (tester) async {
    await tester.pumpWidget(_host(_FailingAuth()));
    final l10n = AppLocalizations.of(
      tester.element(find.byType(EmailOtpScreen)),
    );
    await tester.enterText(find.byType(TextField), 'a@b.c');
    await tester.pump();
    await tester.tap(find.text(l10n.authSendCode));
    await tester.pumpAndSettle();
    expect(find.text(l10n.authError), findsOneWidget);
  });
}
