/// The focused-mode table, mirroring `packages/test-fixtures/modes/layouts.json`
/// (the single source of truth for tabs, Home cards and "More").
/// `test/features/modes/mode_layouts_test.dart` loads that file and fails on
/// any difference. The shell, Home and More read only these constants.
library;

/// Safety-first priority of the user types (P9-R4): the default mode is the
/// chosen type that comes first here.
const kTypePriority = [
  'allergy_diet',
  'health_condition',
  'family',
  'weight_loss',
  'gym',
  'eat_better',
];

/// The mode with no types chosen (or after "Skip for now", P9-R3).
const kDefaultType = 'eat_better';

/// Every destination of the app, in "More" order. Nothing is ever removed:
/// a destination that is not a tab is in More.
const kDestinations = [
  'home',
  'scan',
  'history',
  'family',
  'protein',
  'compare',
  'search',
  'profile',
  'how_we_score',
];

/// Shown first on Home in every mode when any member has an allergen (P9-R7).
const kAlwaysFirstCardWithAllergens = 'allergy_check';

/// One mode's five tabs (home first, scan second, profile last) and its Home
/// cards in order.
class ModeLayout {
  const ModeLayout({required this.tabs, required this.homeCards});

  final List<String> tabs;
  final List<String> homeCards;
}

const kModeLayouts = <String, ModeLayout>{
  'health_condition': ModeLayout(
    tabs: ['home', 'scan', 'history', 'family', 'profile'],
    homeCards: [
      'today_sugar_salt',
      'claims_tip',
      'not_covered',
      'recent_scans',
    ],
  ),
  'family': ModeLayout(
    tabs: ['home', 'scan', 'family', 'history', 'profile'],
    homeCards: ['family_strip', 'weekly_family', 'recent_scans'],
  ),
  'weight_loss': ModeLayout(
    tabs: ['home', 'scan', 'history', 'protein', 'profile'],
    homeCards: ['today_protein', 'today_sugar_salt', 'recent_scans'],
  ),
  'gym': ModeLayout(
    tabs: ['home', 'scan', 'protein', 'compare', 'profile'],
    homeCards: [
      'today_protein',
      'protein_swaps',
      'protein_claims_tip',
      'recent_scans',
    ],
  ),
  'allergy_diet': ModeLayout(
    tabs: ['home', 'scan', 'family', 'search', 'profile'],
    homeCards: ['allergy_check', 'unknown_explainer', 'recent_scans'],
  ),
  'eat_better': ModeLayout(
    tabs: ['home', 'scan', 'compare', 'history', 'profile'],
    homeCards: ['custom_alerts_setup', 'claims_tip', 'recent_scans'],
  ),
};

/// The layout of [mode]; an unknown mode gets the default one.
ModeLayout layoutFor(String mode) =>
    kModeLayouts[mode] ?? kModeLayouts[kDefaultType]!;

/// "More": every destination not in [mode]'s tab bar, in [kDestinations]
/// order.
List<String> moreDestinations(String mode) {
  final tabs = layoutFor(mode).tabs;
  return [
    for (final d in kDestinations)
      if (!tabs.contains(d)) d,
  ];
}

/// Home's cards for [mode]: `allergy_check` first whenever a member has an
/// allergen (P9-R7), then the mode's cards in order.
List<String> homeCardsFor(String mode, {required bool anyMemberHasAllergens}) {
  final cards = layoutFor(mode).homeCards;
  if (!anyMemberHasAllergens) return cards;
  return [
    kAlwaysFirstCardWithAllergens,
    for (final c in cards)
      if (c != kAlwaysFirstCardWithAllergens) c,
  ];
}
