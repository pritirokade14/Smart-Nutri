import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/app_config.dart';
import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/off_attribution.dart';

/// Opens the web app's policy page ([page] is `privacy` or `terms`) in the
/// app's language. Shows a snack bar when it can't be opened.
Future<void> openPolicy(
  BuildContext context,
  WidgetRef ref,
  String page,
) async {
  final l10n = AppLocalizations.of(context);
  final messenger = ScaffoldMessenger.maybeOf(context);
  final uri = ref.read(appConfigProvider).policyUri(page, l10n.localeName);
  var opened = false;
  if (uri != null) {
    try {
      opened = await ref.read(openExternalUrlProvider)(uri);
    } on Object {
      opened = false;
    }
  }
  if (!opened) {
    messenger?.showSnackBar(SnackBar(content: Text(l10n.policyOpenFailed)));
  }
}

/// Links to the privacy policy and the terms of use (pages of the web app).
/// Hidden when the build has no `SITE_URL`.
class PolicyLinks extends ConsumerWidget {
  const PolicyLinks({super.key});

  static const privacyKey = Key('policy-privacy');
  static const termsKey = Key('policy-terms');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    if (ref.watch(appConfigProvider).siteUrl.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    return Wrap(
      spacing: SnTokens.space2,
      children: [
        TextButton.icon(
          key: privacyKey,
          icon: const Icon(
            Icons.open_in_new_rounded,
            size: SnTokens.fontSizeMd,
          ),
          label: Text(l10n.legalPrivacyTitle),
          onPressed: () => openPolicy(context, ref, 'privacy'),
        ),
        TextButton.icon(
          key: termsKey,
          icon: const Icon(
            Icons.open_in_new_rounded,
            size: SnTokens.fontSizeMd,
          ),
          label: Text(l10n.legalTermsTitle),
          onPressed: () => openPolicy(context, ref, 'terms'),
        ),
      ],
    );
  }
}
