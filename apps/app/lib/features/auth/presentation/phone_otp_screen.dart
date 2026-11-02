import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';
import 'otp_form.dart';

/// Only routed when `FEATURE_PHONE_OTP` is true.
class PhoneOtpScreen extends ConsumerWidget {
  const PhoneOtpScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.read(authRepositoryProvider);
    return OtpForm(
      identifierLabel: (l10n) => l10n.authPhoneLabel,
      keyboardType: TextInputType.phone,
      isValidIdentifier: isValidPhone,
      onSend: auth.sendPhoneOtp,
      onVerify: auth.verifyPhoneOtp,
    );
  }
}
