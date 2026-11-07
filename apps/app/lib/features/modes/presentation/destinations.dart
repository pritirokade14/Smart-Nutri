import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';

/// The shell branches, in `StatefulShellRoute` order.
const kShellBranches = ['home', 'diary', 'family', 'protein', 'profile'];

/// The path of each shell branch.
const kBranchPaths = {
  'home': '/home',
  'diary': '/diary',
  'family': '/family',
  'protein': '/protein',
  'profile': '/profile',
};

/// Full-screen routes above the shell: their tabs and More entries push them
/// (Scan as before, so the camera runs only while the scanner is on screen).
const kPushedRoutes = {
  'scan': '/scan',
  'compare': '/compare',
  'search': '/search',
  'how_we_score': '/methodology',
};

String destinationLabel(AppLocalizations l, String key) => switch (key) {
  'home' => l.navHome,
  'scan' => l.navScan,
  'diary' => l.navDiary,
  'family' => l.navFamily,
  'protein' => l.navProtein,
  'compare' => l.navCompare,
  'search' => l.navSearch,
  'profile' => l.navProfile,
  'how_we_score' => l.navHowWeScore,
  _ => key,
};

IconData destinationIcon(String key, {bool selected = false}) => switch (key) {
  'home' => selected ? Icons.home_rounded : Icons.home_outlined,
  'scan' => Icons.qr_code_scanner_rounded,
  'diary' => selected ? Icons.menu_book_rounded : Icons.menu_book_outlined,
  'family' => selected ? Icons.groups_rounded : Icons.groups_outlined,
  'protein' =>
    selected ? Icons.fitness_center_rounded : Icons.fitness_center_outlined,
  'compare' => Icons.compare_arrows_rounded,
  'search' => Icons.search_rounded,
  'profile' => selected ? Icons.person_rounded : Icons.person_outline_rounded,
  _ => Icons.rule_rounded,
};

/// Opens [key]: a shell branch by its path, anything else pushed above the
/// shell.
void openDestination(BuildContext context, String key) {
  final pushed = kPushedRoutes[key];
  if (pushed != null) {
    context.push(pushed);
    return;
  }
  final path = kBranchPaths[key];
  if (path != null) context.go(path);
}
