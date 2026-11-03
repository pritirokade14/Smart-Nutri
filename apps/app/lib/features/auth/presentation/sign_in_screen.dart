import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../core/config/app_config.dart';
import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/brand_illustration.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/google_sign_in_button.dart';
import '../../../shared/widgets/states.dart';
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
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final config = ref.watch(appConfigProvider);
    final phone = config.featurePhoneOtp;
    final email = config.featureEmailOtp;
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) => SingleChildScrollView(
            padding: const EdgeInsets.all(SnTokens.space5),
            child: ConstrainedBox(
              constraints: BoxConstraints(
                minHeight: constraints.maxHeight - SnTokens.space5 * 2,
              ),
              child: IntrinsicHeight(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: SnTokens.space4),
                    const BrandHeroIllustration(),
                    const SizedBox(height: SnTokens.space5),
                    Semantics(
                      header: true,
                      child: Text(
                        l10n.appName,
                        textAlign: TextAlign.center,
                        style: theme.textTheme.displaySmall?.copyWith(
                          color: c.brandStrong,
                        ),
                      ),
                    ),
                    const SizedBox(height: SnTokens.space2),
                    Text(
                      l10n.authTagline,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                    const Spacer(),
                    const SizedBox(height: SnTokens.space6),
                    GoogleSignInButton(
                      label: l10n.authGoogle,
                      busy: _busy,
                      onPressed: _google,
                    ),
                    if (email || phone) ...[
                      const SizedBox(height: SnTokens.space3),
                      _OrDivider(label: l10n.authOr),
                      const SizedBox(height: SnTokens.space3),
                    ],
                    if (email) ...[
                      SecondaryButton(
                        label: l10n.authEmail,
                        icon: Icons.mail_outline_rounded,
                        onPressed: () => context.go('/sign-in/email'),
                      ),
                      const SizedBox(height: SnTokens.space3),
                    ],
                    if (phone)
                      SecondaryButton(
                        label: l10n.authPhone,
                        icon: Icons.phone_outlined,
                        onPressed: () => context.go('/sign-in/phone'),
                      ),
                    if (_failed) ...[
                      const SizedBox(height: SnTokens.space4),
                      InlineErrorBanner(message: l10n.authError),
                    ],
                    const SizedBox(height: SnTokens.space4),
                    const DisclaimerFooter(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _OrDivider extends StatelessWidget {
  const _OrDivider({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Row(
      children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: SnTokens.space3),
          child: Text(
            label,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        ),
        const Expanded(child: Divider()),
      ],
    );
  }
}
