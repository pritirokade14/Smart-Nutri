import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../core/config/app_config.dart';
import '../../../core/l10n/app_localizations.dart';
import '../data/auth_repository.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});

  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  bool _failed = false;
  bool _busy = false;

  Future<void> _google() async {
    setState(() {
      _failed = false;
      _busy = true;
    });
    try {
      await ref.read(authRepositoryProvider).signInWithGoogle();
    } on GoogleSignInException catch (e) {
      // A dismissed Google sheet is not an error.
      if (mounted && e.code != GoogleSignInExceptionCode.canceled) {
        setState(() => _failed = true);
      }
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final config = ref.watch(appConfigProvider);
    final phone = config.featurePhoneOtp;
    final email = config.featureEmailOtp;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.authTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton(
              onPressed: _busy ? null : _google,
              child: Text(l10n.authGoogle),
            ),
            if (email) ...[
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.go('/sign-in/email'),
                child: Text(l10n.authEmail),
              ),
            ],
            if (phone) ...[
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.go('/sign-in/phone'),
                child: Text(l10n.authPhone),
              ),
            ],
            if (_failed) ...[
              const SizedBox(height: 16),
              Text(
                l10n.authError,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const Spacer(),
            Text(l10n.commonDisclaimer, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
