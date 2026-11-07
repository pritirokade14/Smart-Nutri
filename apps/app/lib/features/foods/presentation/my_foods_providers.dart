import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../../recipes/data/recipes_repository.dart';
import '../data/custom_foods_repository.dart';

final customFoodsRepositoryProvider = Provider<CustomFoodsRepository>(
  (ref) => CustomFoodsRepository(ref.watch(apiClientProvider).customFoods),
);

final recipesRepositoryProvider = Provider<RecipesRepository>(
  (ref) => RecipesRepository(ref.watch(apiClientProvider).recipes),
);

/// The pages loaded so far and the cursor of the next one (null: the end).
class Paged<T> {
  const Paged(this.items, this.nextCursor);
  final List<T> items;
  final String? nextCursor;
}

/// The account's custom foods, a page at a time (newest change first).
class CustomFoodsNotifier extends AsyncNotifier<Paged<CustomFoodOut>> {
  bool _loading = false;

  @override
  Future<Paged<CustomFoodOut>> build() async {
    final page = await ref.watch(customFoodsRepositoryProvider).list();
    return Paged(page.items, page.nextCursor);
  }

  Future<void> loadMore() async {
    final now = state.value;
    final cursor = now?.nextCursor;
    if (now == null || cursor == null || _loading) return;
    _loading = true;
    try {
      final page = await ref
          .read(customFoodsRepositoryProvider)
          .list(cursor: cursor);
      state = AsyncData(Paged([...now.items, ...page.items], page.nextCursor));
    } on Object {
      // The list stays as it is; scrolling again retries.
    } finally {
      _loading = false;
    }
  }
}

final customFoodsProvider =
    AsyncNotifierProvider.autoDispose<
      CustomFoodsNotifier,
      Paged<CustomFoodOut>
    >(CustomFoodsNotifier.new, retry: (_, _) => null);

/// The account's recipes, a page at a time.
class RecipesNotifier extends AsyncNotifier<Paged<RecipeSummaryOut>> {
  bool _loading = false;

  @override
  Future<Paged<RecipeSummaryOut>> build() async {
    final page = await ref.watch(recipesRepositoryProvider).list();
    return Paged(page.items, page.nextCursor);
  }

  Future<void> loadMore() async {
    final now = state.value;
    final cursor = now?.nextCursor;
    if (now == null || cursor == null || _loading) return;
    _loading = true;
    try {
      final page = await ref
          .read(recipesRepositoryProvider)
          .list(cursor: cursor);
      state = AsyncData(Paged([...now.items, ...page.items], page.nextCursor));
    } on Object {
      // The list stays as it is; scrolling again retries.
    } finally {
      _loading = false;
    }
  }
}

final recipesProvider =
    AsyncNotifierProvider.autoDispose<RecipesNotifier, Paged<RecipeSummaryOut>>(
      RecipesNotifier.new,
      retry: (_, _) => null,
    );

/// One recipe in full (the builder's edit mode).
final recipeProvider = FutureProvider.autoDispose.family<RecipeOut, String>(
  (ref, id) => ref.watch(recipesRepositoryProvider).get(id),
  retry: (_, _) => null,
);
