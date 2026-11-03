/// The focused-mode table, mirroring `packages/test-fixtures/modes/layouts.json`
/// (the single source of truth). `test/features/modes/mode_layouts_test.dart`
/// loads that file and fails on any difference.
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
