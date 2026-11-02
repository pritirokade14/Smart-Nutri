import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';
import 'otp_form.dart';

class EmailOtpScreen extends ConsumerWidget {
  const EmailOtpScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.read(authRepositoryProvider);
    return OtpForm(
      identifierLabel: (l10n) => l10n.authEmailLabel,
      keyboardType: TextInputType.emailAddress,
      isValidIdentifier: isValidEmail,
      onSend: auth.sendEmailOtp,
      onVerify: auth.verifyEmailOtp,
    );
  }
}
