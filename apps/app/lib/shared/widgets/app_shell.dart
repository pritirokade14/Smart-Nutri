import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// The signed-in shell: a bottom navigation bar over the tab branches
/// (Home, History, Family, Profile). "Scan" is not a branch: it opens the
/// full-screen scanner above the shell, so the camera only runs while the
/// scanner is on screen.
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  /// Bar position of the Scan action.
  static const scanIndex = 1;

  /// Bar position -> branch index (null for Scan).
  static const _branchFor = [0, null, 1, 2, 3];

  static int _barIndexFor(int branch) => _branchFor.indexOf(branch);

  void _onSelected(BuildContext context, int index) {
    final branch = _branchFor[index];
    if (branch == null) {
      context.push('/scan');
      return;
    }
    // Re-selecting the current tab returns it to its first page.
    shell.goBranch(branch, initialLocation: branch == shell.currentIndex);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _barIndexFor(shell.currentIndex),
        onDestinationSelected: (i) => _onSelected(context, i),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home_rounded),
            label: l10n.navHome,
          ),
          NavigationDestination(
            // The scan action stands out in the brand colour.
            icon: Container(
              padding: const EdgeInsets.all(SnTokens.space2),
              decoration: BoxDecoration(color: c.brand, shape: BoxShape.circle),
              child: Icon(
                Icons.qr_code_scanner_rounded,
                color: c.textInverse,
                size: SnTokens.fontSizeLg,
              ),
            ),
            label: l10n.navScan,
          ),
          NavigationDestination(
            icon: const Icon(Icons.history_rounded),
            selectedIcon: const Icon(Icons.history_toggle_off_rounded),
            label: l10n.navHistory,
          ),
          NavigationDestination(
            icon: const Icon(Icons.groups_outlined),
            selectedIcon: const Icon(Icons.groups_rounded),
            label: l10n.navFamily,
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline_rounded),
            selectedIcon: const Icon(Icons.person_rounded),
            label: l10n.navProfile,
          ),
        ],
      ),
    );
  }
}
