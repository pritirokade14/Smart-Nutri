import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/tokens.g.dart';

/// Opens a URL outside the app; overridden in tests.
final openExternalUrlProvider = Provider<Future<bool> Function(Uri)>(
  (ref) =>
      (uri) => launchUrl(uri, mode: LaunchMode.externalApplication),
);

/// Open Food Facts product page for [barcode].
Uri offProductUrl(String barcode) =>
    Uri.https('world.openfoodfacts.org', '/product/$barcode');

/// ODbL credit for data from Open Food Facts, linking to the product page.
/// Show it wherever OFF data is displayed.
class OffAttribution extends ConsumerWidget {
  const OffAttribution({super.key, required this.barcode});

  final String barcode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    return Semantics(
      link: true,
      child: InkWell(
        onTap: () => ref.read(openExternalUrlProvider)(offProductUrl(barcode)),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: SnTokens.space2),
          child: Row(
            children: [
              const Icon(Icons.open_in_new, size: SnTokens.fontSizeMd),
              const SizedBox(width: SnTokens.space2),
              Expanded(
                child: Text(
                  l10n.attributionOff,
                  style: theme.textTheme.bodySmall?.copyWith(
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
