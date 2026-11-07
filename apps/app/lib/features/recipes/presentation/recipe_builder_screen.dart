import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/source_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../../diary/presentation/add_food_sheet.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../foods/data/foods_repository.dart';
import '../../foods/domain/unit_label.dart';
import '../../foods/presentation/food_search_view.dart';
import '../../foods/presentation/my_foods_providers.dart';
import '../../foods/presentation/portion_picker_sheet.dart';
import '../../meals/data/meals_repository.dart';
import '../../meals/domain/meal_draft.dart';
import '../../scan/domain/number_text.dart';
import 'recipe_nutrients.dart';

/// One ingredient of the recipe being built: what it is (exactly one ref),
/// how much, and its name for the list. No nutrient is held here.
class IngredientDraft {
  const IngredientDraft({
    required this.name,
    required this.quantity,
    required this.unit,
    this.foodId,
    this.customFoodId,
    this.productId,
    this.barcode,
    this.available = true,
  });

  final String name;
  final num quantity;
  final String unit;
  final String? foodId;
  final String? customFoodId;
  final String? productId;
  final String? barcode;

  /// False when it was a custom food of yours that has been deleted: it must
  /// be replaced before the recipe can be saved.
  final bool available;

  factory IngredientDraft.fromOut(RecipeIngredientOut i) => IngredientDraft(
    name: i.name,
    quantity: i.quantity,
    unit: i.unit,
    foodId: i.foodId,
    customFoodId: i.customFoodId,
    productId: i.productId,
    barcode: i.barcode,
    available: i.available,
  );

  RecipeIngredientIn toIn() => RecipeIngredientIn(
    foodId: foodId,
    customFoodId: customFoodId,
    productId: productId,
    barcode: barcode,
    quantity: quantity,
    unit: RecipeIngredientInUnit.fromJson(unit),
  );
}

/// The recipe builder: a name, ingredients picked through the food search and
/// portion picker (nothing is logged), the number of servings and the cooked
/// weight. Before it is saved only the ingredient list shows; after it, the
/// API's numbers.
class RecipeBuilderScreen extends ConsumerStatefulWidget {
  const RecipeBuilderScreen({super.key, this.recipeId});

  final String? recipeId;

  static const nameKey = Key('recipe-name');
  static const servingsKey = Key('recipe-servings');
  static const cookedWeightKey = Key('recipe-cooked-weight');
  static const tipKey = Key('recipe-cooked-weight-tip');
  static const addIngredientKey = Key('recipe-add-ingredient');
  static const saveKey = Key('recipe-save');
  static const logKey = Key('recipe-log-serving');
  static const errorKey = Key('recipe-error');
  static const ingredientsKey = Key('recipe-ingredients');
  static Key ingredientKey(int i) => Key('recipe-ingredient-$i');
  static Key unavailableKey(int i) => Key('recipe-ingredient-unavailable-$i');
  static Key replaceKey(int i) => Key('recipe-ingredient-replace-$i');
  static Key removeKey(int i) => Key('recipe-ingredient-remove-$i');

  @override
  ConsumerState<RecipeBuilderScreen> createState() =>
      _RecipeBuilderScreenState();
}

class _RecipeBuilderScreenState extends ConsumerState<RecipeBuilderScreen> {
  final _name = TextEditingController();
  final _servings = TextEditingController();
  final _cooked = TextEditingController();
  final _ingredients = <IngredientDraft>[];

  /// Set by the first save, or the loaded recipe: the API's numbers.
  RecipeOut? _recipe;
  late final String _clientId = const Uuid().v4();
  bool _loaded = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _servings.dispose();
    _cooked.dispose();
    super.dispose();
  }

  void _fill(RecipeOut r) {
    _recipe = r;
    _name.text = r.name;
    _servings.text = r.servings == null ? '' : formatForDisplay(r.servings!);
    _cooked.text = r.cookedWeightG == null
        ? ''
        : formatForDisplay(r.cookedWeightG!);
    _ingredients
      ..clear()
      ..addAll([for (final i in r.ingredients) IngredientDraft.fromOut(i)]);
  }

  bool get _numbersOk => _servingsValue.ok && _cookedValue.ok;
  ({bool ok, num? value}) get _servingsValue => parseNumber(_servings.text);
  ({bool ok, num? value}) get _cookedValue => parseNumber(_cooked.text);

  bool get _canSave =>
      _name.text.trim().isNotEmpty &&
      _ingredients.isNotEmpty &&
      _ingredients.every((i) => i.available) &&
      _numbersOk &&
      !_busy;

  Future<void> _addIngredient({int? replace}) async {
    final hit = await showModalBottomSheet<FoodHit>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: SnTokens.space4,
          right: SnTokens.space4,
          bottom: MediaQuery.viewInsetsOf(ctx).bottom + SnTokens.space4,
        ),
        child: SingleChildScrollView(
          child: FoodSearchView(
            ingredientMode: true,
            onPick: (h) => Navigator.of(ctx).pop(h),
          ),
        ),
      ),
    );
    if (hit == null || !mounted) return;
    final kind = switch (hit.kind) {
      FoodHitKind.food => FoodKindPath.food,
      FoodHitKind.product => FoodKindPath.product,
      FoodHitKind.customFood => FoodKindPath.customFood,
      _ => FoodKindPath.off,
    };
    final memberId = await _memberId() ?? '';
    if (!mounted) return;
    IngredientDraft? picked;
    final saved = await showPortionPicker(
      context,
      food: (kind: kind, id: hit.id),
      name: hit.name,
      memberId: memberId,
      ingredient: true,
      onSave: (c) async {
        picked = IngredientDraft(
          name: hit.name,
          quantity: c.quantity,
          unit: c.unit,
          foodId: kind == FoodKindPath.food ? hit.id : null,
          customFoodId: kind == FoodKindPath.customFood ? hit.id : null,
          productId: kind == FoodKindPath.product ? hit.id : null,
          barcode: kind == FoodKindPath.off ? hit.id : null,
        );
        return true;
      },
    );
    final ingredient = picked;
    if (saved == null || ingredient == null || !mounted) return;
    setState(() {
      if (replace != null) {
        _ingredients[replace] = ingredient;
      } else {
        _ingredients.add(ingredient);
      }
    });
  }

  /// The member whose diary this is (the numbers redaction follows them).
  Future<String?> _memberId() async {
    try {
      return (await ref.read(diaryDayProvider(null).future)).memberId;
    } on Object {
      return null;
    }
  }

  Future<void> _save() async {
    if (!_canSave) return;
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    final body = RecipeIn(
      name: _name.text.trim(),
      servings: _servingsValue.value,
      cookedWeightG: _cookedValue.value,
      ingredients: [for (final i in _ingredients) i.toIn()],
    );
    final repo = ref.read(recipesRepositoryProvider);
    try {
      final id = _recipe?.id ?? widget.recipeId;
      final out = id == null
          ? await repo.create(body, clientId: _clientId)
          : await repo.update(id, body);
      ref.invalidate(recipesProvider);
      if (!mounted) return;
      setState(() {
        _fill(out);
        _busy = false;
      });
      messenger.showSnackBar(SnackBar(content: Text(l10n.recipesSaved)));
    } on FoodsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
      });
    }
  }

  Future<void> _logServing() async {
    final recipe = _recipe;
    if (recipe == null) return;
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final memberId = await _memberId();
    if (!mounted) return;
    if (memberId == null) {
      setState(() => _error = l10n.errorNetwork);
      return;
    }
    final result = await showPortionPicker(
      context,
      food: (kind: FoodKindPath.recipe, id: recipe.id),
      name: recipe.name,
      memberId: memberId,
      onSave: (c) => logDiaryEntry(
        ref,
        MealDraft(
          memberId: memberId,
          recipeId: recipe.id,
          quantity: c.quantity,
          unit: c.unit,
          eatenAt: DateTime.now().toUtc(),
          mealSlotId: c.slotId,
          displayName: recipe.name,
        ),
        'recipe',
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
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final id = widget.recipeId;
    if (id != null && !_loaded) {
      final async = ref.watch(recipeProvider(id));
      final loaded = async.value;
      if (loaded != null) {
        _loaded = true;
        _fill(loaded);
      } else {
        return Scaffold(
          appBar: AppBar(title: Text(l10n.recipesTitle)),
          body: async.hasError
              ? ErrorState(
                  message: localizedErrorCode(
                    l10n,
                    async.error is FoodsFailure
                        ? (async.error! as FoodsFailure).code
                        : apiErrorCode(async.error!),
                  ),
                  onRetry: () => ref.invalidate(recipeProvider(id)),
                )
              : const Padding(
                  padding: EdgeInsets.all(SnTokens.space4),
                  child: LoadingSkeleton(lines: 5),
                ),
        );
      }
    }
    return Scaffold(
      appBar: AppBar(title: Text(l10n.recipesTitle)),
      body: _form(context),
    );
  }

  Widget _form(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    const gap = SizedBox(height: SnTokens.space3);
    final recipe = _recipe;
    return ListView(
      padding: const EdgeInsets.all(SnTokens.space4),
      children: [
        TextField(
          key: RecipeBuilderScreen.nameKey,
          controller: _name,
          enabled: !_busy,
          maxLength: 80,
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            labelText: l10n.recipesName,
            counterText: '',
          ),
        ),
        gap,
        Text(l10n.recipesIngredients, style: theme.textTheme.titleSmall),
        Column(
          key: RecipeBuilderScreen.ingredientsKey,
          children: [
            for (var i = 0; i < _ingredients.length; i++)
              _ingredientTile(l10n, theme, c, i),
          ],
        ),
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: TextButton.icon(
            key: RecipeBuilderScreen.addIngredientKey,
            onPressed: _busy ? null : _addIngredient,
            icon: const Icon(Icons.add_rounded),
            label: Text(l10n.recipesAddIngredient),
          ),
        ),
        gap,
        TextField(
          key: RecipeBuilderScreen.servingsKey,
          controller: _servings,
          enabled: !_busy,
          onChanged: (_) => setState(() {}),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: l10n.recipesServings,
            errorText: _servingsValue.ok ? null : l10n.errorValidationError,
          ),
        ),
        gap,
        TextField(
          key: RecipeBuilderScreen.cookedWeightKey,
          controller: _cooked,
          enabled: !_busy,
          onChanged: (_) => setState(() {}),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: l10n.recipesCookedWeight,
            errorText: _cookedValue.ok ? null : l10n.errorValidationError,
          ),
        ),
        Text(
          l10n.recipesCookedWeightTip,
          key: RecipeBuilderScreen.tipKey,
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
        if (_error != null) ...[
          gap,
          InlineErrorBanner(
            key: RecipeBuilderScreen.errorKey,
            message: _error!,
          ),
        ],
        gap,
        PrimaryButton(
          buttonKey: RecipeBuilderScreen.saveKey,
          label: l10n.customFoodSave,
          icon: Icons.check_rounded,
          busy: _busy,
          onPressed: _canSave ? _save : null,
        ),
        if (recipe != null) ...[
          gap,
          RecipeNutrients(recipe: recipe),
          SourceAttribution(keys: recipe.attributions),
          gap,
          OutlinedButton.icon(
            key: RecipeBuilderScreen.logKey,
            onPressed: _busy ? null : _logServing,
            icon: const Icon(Icons.restaurant_rounded),
            label: Text(l10n.recipesLogServing),
          ),
        ],
      ],
    );
  }

  Widget _ingredientTile(
    AppLocalizations l10n,
    ThemeData theme,
    SnColors c,
    int i,
  ) {
    final ing = _ingredients[i];
    return ListTile(
      key: RecipeBuilderScreen.ingredientKey(i),
      contentPadding: EdgeInsets.zero,
      title: Text(ing.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${formatForDisplay(ing.quantity)} '
            '${unitLabel(l10n, ing.unit, ing.quantity)}',
            style: theme.textTheme.bodySmall,
          ),
          if (!ing.available)
            Text(
              l10n.recipesIngredientUnavailable,
              key: RecipeBuilderScreen.unavailableKey(i),
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (!ing.available)
            IconButton(
              key: RecipeBuilderScreen.replaceKey(i),
              tooltip: l10n.recipesAddIngredient,
              icon: const Icon(Icons.swap_horiz_rounded),
              onPressed: _busy ? null : () => _addIngredient(replace: i),
            ),
          IconButton(
            key: RecipeBuilderScreen.removeKey(i),
            tooltip: l10n.diaryDelete,
            icon: const Icon(Icons.close_rounded),
            onPressed: _busy
                ? null
                : () => setState(() => _ingredients.removeAt(i)),
          ),
        ],
      ),
    );
  }
}
