import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../data/foods_repository.dart';
import 'my_foods_providers.dart';

/// Your custom foods and recipes, a page at a time, with edit and delete.
class MyFoodsScreen extends ConsumerWidget {
  const MyFoodsScreen({super.key});

  static const foodsKey = Key('my-foods-list');
  static const recipesKey = Key('my-recipes-list');
  static const newFoodKey = Key('my-foods-new-food');
  static const newRecipeKey = Key('my-foods-new-recipe');
  static const emptyKey = Key('my-foods-empty');
  static Key foodKey(String id) => Key('my-food-$id');
  static Key recipeKey(String id) => Key('my-recipe-$id');
  static Key deleteFoodKey(String id) => Key('my-food-delete-$id');
  static Key deleteRecipeKey(String id) => Key('my-recipe-delete-$id');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final foods = ref.watch(customFoodsProvider);
    final recipes = ref.watch(recipesProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.foodsMyFoods)),
      body: ListView(
        padding: const EdgeInsets.all(SnTokens.space4),
        children: [
          Wrap(
            spacing: SnTokens.space2,
            children: [
              OutlinedButton.icon(
                key: newFoodKey,
                onPressed: () async {
                  await context.push('/diary/foods/new');
                  ref.invalidate(customFoodsProvider);
                },
                icon: const Icon(Icons.add_rounded),
                label: Text(l10n.foodsNewFood),
              ),
              OutlinedButton.icon(
                key: newRecipeKey,
                onPressed: () async {
                  await context.push('/diary/recipes/new');
                  ref.invalidate(recipesProvider);
                },
                icon: const Icon(Icons.add_rounded),
                label: Text(l10n.foodsNewRecipe),
              ),
            ],
          ),
          const SizedBox(height: SnTokens.space3),
          SectionHeader(
            title: l10n.customFoodTitle,
            icon: Icons.restaurant_rounded,
          ),
          _foods(context, ref, l10n, foods),
          const SizedBox(height: SnTokens.space4),
          SectionHeader(
            title: l10n.recipesTitle,
            icon: Icons.soup_kitchen_outlined,
          ),
          _recipes(context, ref, l10n, recipes),
        ],
      ),
    );
  }

  Widget _error(AppLocalizations l10n, Object e, VoidCallback onRetry) =>
      ErrorState(
        message: localizedErrorCode(
          l10n,
          e is FoodsFailure ? e.code : apiErrorCode(e),
        ),
        onRetry: onRetry,
      );

  Widget _foods(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    AsyncValue<Paged<CustomFoodOut>> async,
  ) => async.when(
    loading: () => const LoadingSkeleton(lines: 2),
    error: (e, _) => _error(l10n, e, () => ref.invalidate(customFoodsProvider)),
    data: (page) => Column(
      key: foodsKey,
      children: [
        for (var i = 0; i < page.items.length; i++)
          _foodTile(context, ref, l10n, page, i),
      ],
    ),
  );

  Widget _foodTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    Paged<CustomFoodOut> page,
    int i,
  ) {
    // The last row asks for the next page when it is drawn.
    if (i == page.items.length - 1 && page.nextCursor != null) {
      Future.microtask(() => ref.read(customFoodsProvider.notifier).loadMore());
    }
    final f = page.items[i];
    return ListTile(
      key: foodKey(f.id),
      contentPadding: EdgeInsets.zero,
      title: Text(f.name),
      subtitle: f.brand == null ? null : Text(f.brand!),
      onTap: () async {
        await context.push('/diary/foods/${f.id}', extra: f);
        ref.invalidate(customFoodsProvider);
      },
      trailing: IconButton(
        key: deleteFoodKey(f.id),
        tooltip: l10n.customFoodDelete,
        icon: const Icon(Icons.delete_outline_rounded),
        onPressed: () => _confirm(
          context,
          l10n,
          l10n.customFoodDeleteConfirm,
          () => ref.read(customFoodsRepositoryProvider).delete(f.id),
          () => ref.invalidate(customFoodsProvider),
        ),
      ),
    );
  }

  Widget _recipes(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    AsyncValue<Paged<RecipeSummaryOut>> async,
  ) => async.when(
    loading: () => const LoadingSkeleton(lines: 2),
    error: (e, _) => _error(l10n, e, () => ref.invalidate(recipesProvider)),
    data: (page) {
      if (page.items.isEmpty) {
        return Padding(
          key: emptyKey,
          padding: const EdgeInsets.all(SnTokens.space3),
          child: Text(
            l10n.recipesEmpty,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: SnColors.of(context).textSecondary,
            ),
          ),
        );
      }
      return Column(
        key: recipesKey,
        children: [
          for (var i = 0; i < page.items.length; i++)
            _recipeTile(context, ref, l10n, page, i),
        ],
      );
    },
  );

  Widget _recipeTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    Paged<RecipeSummaryOut> page,
    int i,
  ) {
    if (i == page.items.length - 1 && page.nextCursor != null) {
      Future.microtask(() => ref.read(recipesProvider.notifier).loadMore());
    }
    final r = page.items[i];
    return ListTile(
      key: recipeKey(r.id),
      contentPadding: EdgeInsets.zero,
      title: Text(r.name),
      onTap: () async {
        await context.push('/diary/recipes/${r.id}');
        ref.invalidate(recipesProvider);
      },
      trailing: IconButton(
        key: deleteRecipeKey(r.id),
        tooltip: l10n.diaryDelete,
        icon: const Icon(Icons.delete_outline_rounded),
        onPressed: () => _confirm(
          context,
          l10n,
          l10n.recipesDeleteConfirm,
          () => ref.read(recipesRepositoryProvider).delete(r.id),
          () => ref.invalidate(recipesProvider),
        ),
      ),
    );
  }

  Future<void> _confirm(
    BuildContext context,
    AppLocalizations l10n,
    String message,
    Future<void> Function() delete,
    VoidCallback done,
  ) async {
    final messenger = ScaffoldMessenger.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l10n.commonCancel),
          ),
          TextButton(
            key: const Key('my-foods-delete-confirm'),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l10n.diaryDelete),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await delete();
      done();
    } on FoodsFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }
}
