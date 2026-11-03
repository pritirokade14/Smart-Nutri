import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../shared/widgets/states.dart';

/// Family tab. A placeholder until family member profiles ship.
class FamilyScreen extends StatelessWidget {
  const FamilyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return ComingSoonScaffold(
      title: l10n.familyTitle,
      icon: Icons.groups_rounded,
      headline: l10n.familyComingSoonTitle,
      body: l10n.familyComingSoonBody,
    );
  }
}
