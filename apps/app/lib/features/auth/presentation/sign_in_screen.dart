import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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

  Future<void> _google() async {
    setState(() => _failed = false);
    try {
      await ref.read(authRepositoryProvider).signInWithGoogle();
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final phone = ref.watch(appConfigProvider).featurePhoneOtp;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.authTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton(onPressed: _google, child: Text(l10n.authGoogle)),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () => context.go('/sign-in/email'),
              child: Text(l10n.authEmail),
            ),
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
                l10n.errorInternalError,
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
