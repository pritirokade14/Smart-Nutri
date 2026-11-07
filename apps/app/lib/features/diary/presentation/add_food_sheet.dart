import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';
import 'package:uuid/uuid.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/source_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../../favourites/data/favourites_repository.dart';
import '../../favourites/presentation/favourite_star.dart';
import '../../favourites/presentation/favourites_providers.dart';
import '../../favourites/presentation/favourites_segment.dart';
import '../../foods/data/foods_repository.dart';
import '../../foods/domain/portion_line.dart';
import '../../foods/presentation/food_search_view.dart';
import '../../foods/presentation/portion_picker_sheet.dart';
import '../../meals/data/meals_repository.dart';
import '../../meals/domain/meal_draft.dart';
import '../../meals/presentation/meals_providers.dart';
import '../domain/diary_dates.dart';
import '../domain/slot_label.dart';
import 'diary_providers.dart';
import 'quick_add_form.dart';

/// Where the sheet sends the user next: the existing flows.
enum AddFoodNext { barcode, label }

enum _Segment { recent, favourites, search, barcode, label, quick, create }

/// Logs [draft] (online or queued) and sends `diary_entry_added` with the
/// method only. Throws [MealsFailure] when the API refuses it.
Future<MealLogResult> logDiaryEntry(
  WidgetRef ref,
  MealDraft draft,
  String method,
) async {
  final result = await ref.read(mealsRepositoryProvider).log(draft);
  ref.read(mealsRevisionProvider.notifier).bump();
  // The method only: no name, slot label, nutrient or portion.
  await ref.read(analyticsProvider).track('diary_entry_added', {
    'method': method,
  });
  return result;
}

/// Opens the add-food sheet for [day]. [slotId] preselects a slot (its Add
/// button); without it the API's suggestion is preselected. Returns the
/// flow the user chose, or null.
Future<AddFoodNext?> showAddFoodSheet(
  BuildContext context, {
  required DiaryDayOut day,
  String? slotId,
}) => showModalBottomSheet<AddFoodNext>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => AddFoodSheet(day: day, slotId: slotId),
);

class AddFoodSheet extends ConsumerStatefulWidget {
  const AddFoodSheet({super.key, required this.day, this.slotId});

  final DiaryDayOut day;
  final String? slotId;

  static Key segmentKey(String name) => Key('add-food-segment-$name');
  static Key chipKey(String slotId) => Key('add-food-slot-$slotId');
  static const newFoodKey = Key('add-food-new-food');
  static const newRecipeKey = Key('add-food-new-recipe');
  static Key recentKey(String productId) => Key('add-food-recent-$productId');

  @override
  ConsumerState<AddFoodSheet> createState() => _AddFoodSheetState();
}

class _AddFoodSheetState extends ConsumerState<AddFoodSheet> {
  _Segment _segment = _Segment.recent;
  String? _picked;
  bool _busy = false;
  String? _error;

  /// One `client_id` per favourite meal action; kept for retries, dropped on
  /// success.
  final _logAgainIds = <String, String>{};

  /// A past day sends `local_date`; today sends the time (the API decides
  /// which day is today).
  String? get _localDate =>
      dateKey(widget.day.date) == dateKey(widget.day.today)
      ? null
      : dateKey(widget.day.date);

  /// The slot to send: the chip, else the tapped slot, else none (the API
  /// picks one).
  String? _slot(MealSlotsOut? slots) =>
      _picked ?? widget.slotId ?? slots?.suggestedSlotId;

  /// Opens the portion picker for a search hit; a saved choice closes the
  /// sheet like any other log.
  Future<void> _pick(FoodHit hit, String? slotId) => _pickRef(
    (
      kind: switch (hit.kind) {
        FoodHitKind.food => FoodKindPath.food,
        FoodHitKind.product => FoodKindPath.product,
        FoodHitKind.customFood => FoodKindPath.customFood,
        FoodHitKind.recipe => FoodKindPath.recipe,
        _ => FoodKindPath.off,
      },
      id: hit.id,
    ),
    hit.name,
    slotId,
  );

  Future<void> _pickRef(FoodRef food, String name, String? slotId) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    final kind = food.kind;
    final hit = (id: food.id, name: name);
    final result = await showPortionPicker(
      context,
      food: (kind: kind, id: hit.id),
      name: hit.name,
      memberId: widget.day.memberId,
      slotId: slotId,
      onSave: (c) => logDiaryEntry(
        ref,
        MealDraft(
          memberId: widget.day.memberId,
          foodId: kind == FoodKindPath.food ? hit.id : null,
          productId: kind == FoodKindPath.product ? hit.id : null,
          customFoodId: kind == FoodKindPath.customFood ? hit.id : null,
          recipeId: kind == FoodKindPath.recipe ? hit.id : null,
          barcode: kind == FoodKindPath.off ? hit.id : null,
          quantity: c.quantity,
          unit: c.unit,
          eatenAt: DateTime.now().toUtc(),
          mealSlotId: c.slotId,
          localDate: _localDate,
          displayName: hit.name,
        ),
        // Your own foods and recipes have their own method value.
        switch (kind) {
          FoodKindPath.customFood => 'custom',
          FoodKindPath.recipe => 'recipe',
          _ => 'search',
        },
      ),
    );
    if (result == null) return;
    messenger.showSnackBar(
      SnackBar(
        content: Text(
          result is MealLogged
              ? l10n.mealsLogSavedYou
              : l10n.mealsQueuedOffline,
        ),
      ),
    );
    if (mounted) nav.pop();
  }

  /// A food favourite: one tap logs its default portion (queued offline).
  Future<void> _logFavouriteFood(FavouriteOut f, String? slotId) {
    final ref = favouriteFoodRef(f);
    if (ref == null) return Future.value();
    return _log(
      MealDraft(
        memberId: widget.day.memberId,
        foodId: ref.kind == FoodKindPath.food ? ref.id : null,
        productId: ref.kind == FoodKindPath.product ? ref.id : null,
        customFoodId: ref.kind == FoodKindPath.customFood ? ref.id : null,
        recipeId: ref.kind == FoodKindPath.recipe ? ref.id : null,
        barcode: ref.kind == FoodKindPath.off ? ref.id : null,
        quantity: f.defaultQuantity,
        unit: f.defaultUnit,
        eatenAt: DateTime.now().toUtc(),
        mealSlotId: slotId,
        localDate: _localDate,
        displayName: f.name,
      ),
      'favourite',
    );
  }

  /// A long press: the portion picker.
  Future<void> _pickFavouriteFood(FavouriteOut f, String? slotId) async {
    final food = favouriteFoodRef(f);
    if (food == null) return;
    await _pickRef(food, f.name, slotId);
  }

  /// A meal favourite: "Log again", online only. The count is the only thing
  /// the toast says.
  Future<void> _logFavouriteMeal(FavouriteOut f, String? slotId) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    final clientId = _logAgainIds.putIfAbsent(f.id, () => const Uuid().v4());
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final created = await ref
          .read(favouritesRepositoryProvider)
          .log(f.id, clientId: clientId, slotId: slotId, localDate: _localDate);
      _logAgainIds.remove(f.id);
      ref.read(mealsRevisionProvider.notifier).bump();
      await ref.read(analyticsProvider).track('diary_entry_added', {
        'method': 'favourite',
      });
      messenger.showSnackBar(
        SnackBar(content: Text(l10n.favouritesMealItems(created.length))),
      );
      if (mounted) nav.pop();
    } on FavouritesFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  Future<void> _log(MealDraft draft, String method) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await logDiaryEntry(ref, draft, method);
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            result is MealLogged
                ? l10n.mealsLogSavedYou
                : l10n.mealsQueuedOffline,
          ),
        ),
      );
      if (mounted) nav.pop();
    } on MealsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final slots = ref.watch(mealSlotsProvider).value;
    final slotId = _slot(slots);
    final labels = <_Segment, String>{
      _Segment.recent: l10n.foodsRecent,
      _Segment.favourites: l10n.foodsFavourites,
      _Segment.search: l10n.searchTitle,
      _Segment.barcode: l10n.navScan,
      _Segment.label: l10n.labelTitle,
      _Segment.quick: l10n.foodsQuickAdd,
      _Segment.create: l10n.foodsMyFoods,
    };
    return Padding(
      padding: EdgeInsets.only(
        left: SnTokens.space4,
        right: SnTokens.space4,
        bottom: MediaQuery.viewInsetsOf(context).bottom + SnTokens.space4,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.diaryAdd, style: theme.textTheme.titleLarge),
            const SizedBox(height: SnTokens.space3),
            // Hidden when the slot list has not loaded: the API picks.
            if (slots != null) ...[
              Wrap(
                spacing: SnTokens.space2,
                runSpacing: SnTokens.space2,
                children: [
                  for (final s in slots.items.where((s) => !s.archived))
                    ChoiceChip(
                      key: AddFoodSheet.chipKey(s.id),
                      label: Text(
                        slotLabel(
                          l10n,
                          labelKey: s.labelKey,
                          customLabel: s.customLabel,
                        ),
                      ),
                      selected: s.id == slotId,
                      onSelected: _busy
                          ? null
                          : (_) => setState(() => _picked = s.id),
                    ),
                ],
              ),
              const SizedBox(height: SnTokens.space3),
            ],
            Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space2,
              children: [
                for (final seg in _Segment.values)
                  ChoiceChip(
                    key: AddFoodSheet.segmentKey(seg.name),
                    label: Text(labels[seg]!),
                    selected: seg == _segment,
                    onSelected: (_) => _onSegment(seg, slotId),
                  ),
              ],
            ),
            const SizedBox(height: SnTokens.space3),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: SnTokens.space2),
                child: InlineErrorBanner(message: _error!),
              ),
            if (_segment == _Segment.recent) _recents(slotId),
            if (_segment == _Segment.favourites)
              FavouritesSegment(
                memberId: widget.day.memberId,
                enabled: !_busy,
                onLogFood: (f) => _logFavouriteFood(f, slotId),
                onPickFood: (f) => _pickFavouriteFood(f, slotId),
                onLogMeal: (f) => _logFavouriteMeal(f, slotId),
              ),
            if (_segment == _Segment.search)
              FoodSearchView(
                enabled: !_busy,
                onPick: (hit) => _pick(hit, slotId),
              ),
            if (_segment == _Segment.create) _create(),
            if (_segment == _Segment.quick)
              QuickAddForm(
                busy: _busy,
                onSubmit: (v) => _log(
                  MealDraft(
                    memberId: widget.day.memberId,
                    eatenAt: DateTime.now().toUtc(),
                    mealSlotId: slotId,
                    localDate: _localDate,
                    quickName: v.name,
                    quickEnergyKcal: v.energyKcal,
                    quickProteinG: v.proteinG,
                    quickFatG: v.fatG,
                    quickCarbsG: v.carbsG,
                    quickFibreG: v.fibreG,
                    displayName: v.name,
                  ),
                  'quick_add',
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _onSegment(_Segment seg, String? slotId) {
    switch (seg) {
      case _Segment.barcode:
        _leave(AddFoodNext.barcode, 'barcode', slotId);
      case _Segment.label:
        _leave(AddFoodNext.label, 'label', slotId);
      case _Segment.recent:
      case _Segment.favourites:
      case _Segment.search:
      case _Segment.quick:
      case _Segment.create:
        setState(() => _segment = seg);
    }
  }

  /// The existing search, scanner and label flows take over; their portion
  /// step logs into this slot and day.
  void _leave(AddFoodNext next, String method, String? slotId) {
    ref
        .read(diaryAddContextProvider.notifier)
        .set(
          DiaryAddContext(
            method: method,
            slotId: slotId,
            localDate: _localDate,
            memberId: widget.day.memberId,
          ),
        );
    Navigator.of(context).pop(next);
  }

  /// A create form is a screen of its own: close the sheet, then open it.
  void _open(String path) {
    final router = GoRouter.of(context);
    Navigator.of(context).pop();
    router.push(path);
  }

  Widget _create() {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton.icon(
          key: AddFoodSheet.newFoodKey,
          onPressed: () => _open('/diary/foods/new'),
          icon: const Icon(Icons.add_rounded),
          label: Text(l10n.foodsNewFood),
        ),
        const SizedBox(height: SnTokens.space2),
        OutlinedButton.icon(
          key: AddFoodSheet.newRecipeKey,
          onPressed: () => _open('/diary/recipes/new'),
          icon: const Icon(Icons.add_rounded),
          label: Text(l10n.foodsNewRecipe),
        ),
      ],
    );
  }

  Widget _recents(String? slotId) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(diaryRecentsProvider(slotId))
        .when(
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(l10n, apiErrorCode(e)),
            onRetry: () => ref.invalidate(diaryRecentsProvider(slotId)),
          ),
          data: (items) => Column(
            children: [
              for (final r in items)
                ListTile(
                  key: AddFoodSheet.recentKey(
                    r.foodId ??
                        r.customFoodId ??
                        r.recipeId ??
                        r.productId ??
                        r.barcode ??
                        r.name,
                  ),
                  contentPadding: EdgeInsets.zero,
                  enabled: !_busy,
                  title: Text(r.name),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_recentPortion(l10n, r)),
                      SourceAttribution(
                        keys: recentAttributions(r),
                        offBarcode: r.barcode,
                      ),
                    ],
                  ),
                  trailing: _recentRef(r) == null
                      ? null
                      : FavouriteStar(
                          food: _recentRef(r)!,
                          favouriteId: r.favouriteId,
                          memberId: widget.day.memberId,
                          quantity: r.unit != null ? r.quantity : null,
                          unit: r.quantity != null ? r.unit : null,
                        ),
                  onTap: () => _log(_recentDraft(r, slotId), 'recent'),
                ),
            ],
          ),
        );
  }

  /// The food a recent points at (for its star).
  FoodRef? _recentRef(RecentItem r) {
    if (r.foodId != null) return (kind: FoodKindPath.food, id: r.foodId!);
    if (r.customFoodId != null) {
      return (kind: FoodKindPath.customFood, id: r.customFoodId!);
    }
    if (r.recipeId != null) return (kind: FoodKindPath.recipe, id: r.recipeId!);
    if (r.productId != null) {
      return (kind: FoodKindPath.product, id: r.productId!);
    }
    if (r.barcode != null) return (kind: FoodKindPath.off, id: r.barcode!);
    return null;
  }

  /// A recent logs again what was last eaten: its quantity and unit, or the
  /// resolved amount (grams, or millilitres for an ml food) for a row logged
  /// before household units.
  MealDraft _recentDraft(RecentItem r, String? slotId) {
    final byUnit = r.unit != null && r.quantity != null;
    final ml = r.basis == RecentItemBasis.ml;
    final own =
        r.foodId == null && r.customFoodId == null && r.recipeId == null;
    return MealDraft(
      memberId: widget.day.memberId,
      foodId: r.foodId,
      customFoodId: r.customFoodId,
      recipeId: r.recipeId,
      productId: own ? r.productId : null,
      barcode: own && r.productId == null ? r.barcode : null,
      // An ml amount is sent as millilitres, never as grams.
      grams: byUnit || ml ? null : r.grams,
      quantity: byUnit ? r.quantity : (ml ? r.grams : null),
      unit: byUnit ? r.unit : (ml ? 'ml' : null),
      eatenAt: DateTime.now().toUtc(),
      mealSlotId: slotId,
      localDate: _localDate,
      displayName: r.name,
    );
  }

  String _recentPortion(AppLocalizations l10n, RecentItem r) => portionLine(
    l10n,
    amount: r.grams,
    ml: r.basis == RecentItemBasis.ml,
    quantity: r.quantity,
    unit: r.unit,
    approx: isApproxUnitSource(r.unitSource?.json),
  );
}

/// The credit keys of a recent: its own list, else Open Food Facts when only
/// the older single `attribution` is set.
List<String> recentAttributions(RecentItem r) {
  final list = r.attributions;
  if (list != null && list.isNotEmpty) return list;
  return r.attribution != null ? const [SourceAttribution.offKey] : const [];
}
