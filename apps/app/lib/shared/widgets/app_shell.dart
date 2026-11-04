import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';
import '../../features/modes/mode_layouts.dart';
import '../../features/modes/mode_providers.dart';
import '../../features/modes/presentation/destinations.dart';

/// The signed-in shell: a bottom navigation bar of the focused mode's five
/// tabs (`kModeLayouts[mode].tabs`) over the branches Home, History, Family,
/// Protein and Profile. Scan (always tab 2), Compare and Search are not
/// branches: their tabs push full-screen routes above the shell, so the
/// camera only runs while the scanner is on screen. A branch that is not in
/// the bar (opened from More) shows the bar with Home selected.
class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  /// Bar position of the Scan action (the same in every mode).
  static const scanIndex = 1;

  void _onSelected(BuildContext context, String key) {
    final branch = kShellBranches.indexOf(key);
    if (branch < 0) {
      openDestination(context, key);
      return;
    }
    // Re-selecting the current tab returns it to its first page.
    shell.goBranch(branch, initialLocation: branch == shell.currentIndex);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final tabs = layoutFor(ref.watch(activeModeProvider)).tabs;
    final current = kShellBranches[shell.currentIndex];
    final selected = tabs.indexOf(current);
    return Scaffold(
      body: shell,
      bottomNavigationBar: Semantics(
        label: l10n.navLabel,
        container: true,
        child: NavigationBar(
          selectedIndex: selected < 0 ? 0 : selected,
          onDestinationSelected: (i) => _onSelected(context, tabs[i]),
          destinations: [
            for (final key in tabs)
              if (key == 'scan')
                NavigationDestination(
                  // The scan action stands out in the brand colour.
                  icon: Container(
                    padding: const EdgeInsets.all(SnTokens.space2),
                    decoration: BoxDecoration(
                      color: c.brand,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      destinationIcon(key),
                      color: c.textInverse,
                      size: SnTokens.fontSizeLg,
                    ),
                  ),
                  label: destinationLabel(l10n, key),
                )
              else
                NavigationDestination(
                  icon: Icon(destinationIcon(key)),
                  selectedIcon: Icon(destinationIcon(key, selected: true)),
                  label: destinationLabel(l10n, key),
                ),
          ],
        ),
      ),
    );
  }
}
