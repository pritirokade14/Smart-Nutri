import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../shared/widgets/states.dart';

/// History tab. A placeholder until the history feature ships.
class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return ComingSoonScaffold(
      title: l10n.historyTitle,
      icon: Icons.history_rounded,
      headline: l10n.historyComingSoonTitle,
      body: l10n.historyComingSoonBody,
    );
  }
}
