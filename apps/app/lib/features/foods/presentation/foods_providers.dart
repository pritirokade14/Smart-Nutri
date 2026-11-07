import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../data/foods_repository.dart';

final foodsRepositoryProvider = Provider<FoodsRepository>(
  (ref) => FoodsRepository(ref.watch(apiClientProvider).foods),
);

/// Search results for a (debounced, trimmed) query. No automatic retry.
final foodSearchProvider = FutureProvider.autoDispose
    .family<FoodSearchOut, String>(
      (ref, q) => ref.watch(foodsRepositoryProvider).search(q),
      retry: (_, _) => null,
    );

/// One food with its units, for a member (numbers redaction follows them).
typedef FoodDetailKey = ({FoodRef food, String? memberId});

final foodDetailProvider = FutureProvider.autoDispose
    .family<FoodDetailOut, FoodDetailKey>(
      (ref, key) => ref
          .watch(foodsRepositoryProvider)
          .detail(key.food, memberId: key.memberId),
      retry: (_, _) => null,
    );

/// The household units, for the custom food form's own measures.
final foodUnitsProvider = FutureProvider.autoDispose<List<UnitOut>>(
  (ref) => ref.watch(foodsRepositoryProvider).units(),
  retry: (_, _) => null,
);
