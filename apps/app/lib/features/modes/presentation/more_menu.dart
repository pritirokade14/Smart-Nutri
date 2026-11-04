import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../mode_layouts.dart';
import '../mode_providers.dart';
import 'destinations.dart';

/// "More" (P9-R6): every destination that is not in the current tab bar, so
/// nothing is ever out of reach. A bottom sheet from Home's header and the
/// first section of Profile.
class MoreList extends ConsumerWidget {
  const MoreList({super.key, this.onSelect});

  /// Opens a destination; null opens it from this list's context.
  final void Function(String destination)? onSelect;

  static Key itemKey(String destination) => Key('more-$destination');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final items = moreDestinations(ref.watch(activeModeProvider));
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final d in items)
          ListTile(
            key: itemKey(d),
            leading: Icon(destinationIcon(d), color: c.brandStrong),
            title: Text(destinationLabel(l10n, d)),
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => (onSelect ?? (d) => openDestination(context, d))(d),
          ),
      ],
    );
  }
}

/// Opens "More" as a bottom sheet.
Future<void> showMoreMenu(BuildContext context) {
  final outer = context;
  return showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    useSafeArea: true,
    isScrollControlled: true,
    builder: (sheet) {
      final l10n = AppLocalizations.of(sheet);
      return SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: SnTokens.space4),
              child: Text(
                l10n.modesMoreTitle,
                style: Theme.of(sheet).textTheme.titleLarge,
              ),
            ),
            // Navigates with the page's context once the sheet is closed.
            MoreList(
              onSelect: (d) {
                Navigator.of(sheet).pop();
                if (outer.mounted) openDestination(outer, d);
              },
            ),
          ],
        ),
      );
    },
  );
}
