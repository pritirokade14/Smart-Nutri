import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../auth/data/auth_repository.dart';
import 'consents_section.dart';

/// Profile tab: consents (grant or withdraw) and signing out. Language and
/// account settings are still to come.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.profileTitle)),
      body: ListView(
        padding: const EdgeInsets.all(SnTokens.space4),
        children: [
          const ConsentsSection(),
          EmptyState(
            icon: Icons.manage_accounts_rounded,
            title: l10n.profileComingSoonTitle,
            body: l10n.profileComingSoonBody,
            action: const ComingSoonPill(),
          ),
          SecondaryButton(
            label: l10n.authSignOut,
            icon: Icons.logout_rounded,
            onPressed: () => ref.read(authRepositoryProvider).signOut(),
          ),
        ],
      ),
    );
  }
}
