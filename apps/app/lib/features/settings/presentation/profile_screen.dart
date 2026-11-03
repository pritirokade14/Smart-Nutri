import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../auth/data/auth_repository.dart';

/// Profile tab. Settings are a placeholder for now; signing out works.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return ComingSoonScaffold(
      title: l10n.profileTitle,
      icon: Icons.manage_accounts_rounded,
      headline: l10n.profileComingSoonTitle,
      body: l10n.profileComingSoonBody,
      extra: [
        const SizedBox(height: SnTokens.space4),
        SecondaryButton(
          label: l10n.authSignOut,
          icon: Icons.logout_rounded,
          onPressed: () => ref.read(authRepositoryProvider).signOut(),
        ),
      ],
    );
  }
}
