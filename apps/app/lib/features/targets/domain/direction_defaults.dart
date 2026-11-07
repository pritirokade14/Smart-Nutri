/// The goal direction the setup preselects for a member goal. Mirrors
/// `packages/test-fixtures/targets/direction_defaults.json` (a test keeps
/// them equal); the API's `default_direction` is the source.
const kDirectionForGoal = <String, String>{
  'build_muscle': 'gain',
  'weight_loss': 'lose',
  'healthy_eating': 'maintain',
  'weight_gain': 'gain',
  'none': 'maintain',
};

/// The preselected direction for [goal] (null or unknown is `none`).
String directionForGoal(String? goal) =>
    kDirectionForGoal[goal] ?? kDirectionForGoal['none']!;
