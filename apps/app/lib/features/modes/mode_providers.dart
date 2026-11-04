import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../user_types/domain/user_types.dart';
import '../user_types/presentation/user_types_providers.dart';
import 'mode_layouts.dart';

/// The focused mode: the API's `active_type`. While loading, on an error or
/// offline it is the last value loaded in this session, else [kDefaultType].
/// The mode only arranges the app; it never reaches a verdict.
final activeModeProvider = Provider<String>((ref) {
  final out = ref.watch(userTypesProvider).value;
  if (out == null) return kDefaultType;
  final mode = activeTypeOf(out);
  return kModeLayouts.containsKey(mode) ? mode : kDefaultType;
});

/// The account's chosen types (tap order); the mode switcher shows when
/// there are two or more.
final chosenTypesProvider = Provider<List<String>>((ref) {
  final out = ref.watch(userTypesProvider).value;
  if (out == null) return const [];
  return [
    for (final t in chosenTypes(out))
      if (kModeLayouts.containsKey(t)) t,
  ];
});
