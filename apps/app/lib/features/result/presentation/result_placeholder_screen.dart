import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';

/// Placeholder until the real result screen replaces it (Plan 3 Task 7).
class ResultPlaceholderScreen extends StatelessWidget {
  const ResultPlaceholderScreen({super.key, required this.barcode});

  final String barcode;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.scanTitle)),
      body: Padding(
        padding: const EdgeInsets.all(SnTokens.space5),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(barcode, textAlign: TextAlign.center),
            const SizedBox(height: SnTokens.space4),
            Text(l10n.commonDisclaimer, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
