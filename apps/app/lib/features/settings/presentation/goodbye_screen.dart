import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';

/// Shown, signed out, after the account is deleted.
class GoodbyeScreen extends StatelessWidget {
  const GoodbyeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(SnTokens.space5),
            child: EmptyState(
              icon: Icons.check_circle_outline_rounded,
              title: l10n.goodbyeTitle,
              body: l10n.goodbyeBody,
              action: PrimaryButton(
                label: l10n.goodbyeAction,
                onPressed: () => context.go('/sign-in'),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
