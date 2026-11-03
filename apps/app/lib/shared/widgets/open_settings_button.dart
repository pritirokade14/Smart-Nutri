import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/platform/app_settings.dart';
import 'buttons.dart';

/// "Open settings", shown when a permission is permanently denied.
class OpenSettingsButton extends ConsumerWidget {
  const OpenSettingsButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return SecondaryButton(
      label: l10n.commonOpenSettings,
      icon: Icons.settings_outlined,
      onPressed: () => ref.read(appSettingsProvider).open(),
    );
  }
}
