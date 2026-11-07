import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/widgets/source_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../../foods/data/foods_repository.dart';
import '../../foods/domain/portion_line.dart';
import '../../foods/domain/unit_label.dart';
import '../../scan/domain/number_text.dart';
import 'favourite_star.dart';
import 'favourites_providers.dart';

/// Which food a food favourite points at.
FoodRef? favouriteFoodRef(FavouriteOut f) {
  if (f.foodId != null) return (kind: FoodKindPath.food, id: f.foodId!);
  if (f.customFoodId != null) {
    return (kind: FoodKindPath.customFood, id: f.customFoodId!);
  }
  if (f.recipeId != null) return (kind: FoodKindPath.recipe, id: f.recipeId!);
  if (f.productId != null) {
    return (kind: FoodKindPath.product, id: f.productId!);
  }
  if (f.barcode != null) return (kind: FoodKindPath.off, id: f.barcode!);
  return null;
}

/// The Favourites list of the add-food sheet. It only shows; the sheet logs.
/// A food row shows its name and default portion (no nutrient value anywhere,
/// so nothing to hide) with its data credit. A meal row shows the name exactly
/// as typed and its item count.
class FavouritesSegment extends ConsumerWidget {
  const FavouritesSegment({
    super.key,
    required this.memberId,
    required this.enabled,
    required this.onLogFood,
    required this.onPickFood,
    required this.onLogMeal,
  });

  final String? memberId;
  final bool enabled;
  final void Function(FavouriteOut f) onLogFood;
  final void Function(FavouriteOut f) onPickFood;
  final void Function(FavouriteOut f) onLogMeal;

  static const emptyKey = Key('favourites-empty');
  static Key rowKey(String id) => Key('favourite-row-$id');
  static Key logAgainKey(String id) => Key('favourite-log-again-$id');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(favouritesProvider(memberId))
        .when(
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(l10n, apiErrorCode(e)),
            onRetry: () => ref.invalidate(favouritesProvider(memberId)),
          ),
          data: (items) => items.isEmpty
              ? Padding(
                  key: emptyKey,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: Text(l10n.favouritesEmpty),
                )
              : Column(
                  children: [
                    for (final f in items)
                      f.kind == FavouriteOutKind.meal
                          ? _meal(context, l10n, f)
                          : _food(context, l10n, f),
                  ],
                ),
        );
  }

  Widget _food(BuildContext context, AppLocalizations l10n, FavouriteOut f) {
    final ref = favouriteFoodRef(f);
    final q = f.defaultQuantity;
    final u = f.defaultUnit;
    return ListTile(
      key: rowKey(f.id),
      contentPadding: EdgeInsets.zero,
      enabled: enabled,
      // Food names come from the data and are shown as stored.
      title: Text(f.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (q != null && u != null)
            Text('${formatForDisplay(q)} ${unitLabel(l10n, u, q)}'),
          SourceAttribution(
            keys: f.attributions ?? const [],
            offBarcode: f.barcode,
          ),
        ],
      ),
      trailing: ref == null
          ? null
          : FavouriteStar(
              food: ref,
              favouriteId: f.id,
              memberId: memberId,
              onChanged: (_) {},
            ),
      onTap: () => onLogFood(f),
      onLongPress: () => onPickFood(f),
    );
  }

  Widget _meal(
    BuildContext context,
    AppLocalizations l10n,
    FavouriteOut f,
  ) => ListTile(
    key: rowKey(f.id),
    contentPadding: EdgeInsets.zero,
    enabled: enabled,
    // User text: shown exactly as typed, never translated.
    title: Text(f.name),
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.favouritesMealItems(f.itemCount)),
        for (final i in f.items ?? const <FavouriteItemOut>[])
          if (i.grams != null)
            // Item names are stored data; the amount is in the item's
            // own basis (ml for an ml food), as the API resolved it.
            Text(
              '${i.name ?? ''} · ${portionLine(l10n, amount: i.grams!, ml: i.basis == FavouriteItemOutBasis.ml, quantity: i.quantity, unit: i.unit)}',
            ),
      ],
    ),
    trailing: TextButton(
      key: logAgainKey(f.id),
      onPressed: enabled ? () => onLogMeal(f) : null,
      child: Text(l10n.favouritesLogAgain),
    ),
  );
}
