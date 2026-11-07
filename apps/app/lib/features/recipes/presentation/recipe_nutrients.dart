import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../scan/domain/number_text.dart';

const _rows = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'sugars_g',
  'fat_g',
  'sat_fat_g',
  'fibre_g',
  'salt_g',
];

num? _value(NutrientSnapshot n, String key) => switch (key) {
  'energy_kcal' => n.energyKcal,
  'protein_g' => n.proteinG,
  'carbs_g' => n.carbsG,
  'sugars_g' => n.sugarsG,
  'fat_g' => n.fatG,
  'sat_fat_g' => n.satFatG,
  'fibre_g' => n.fibreG,
  _ => n.saltG,
};

/// A recipe's numbers exactly as the API sent them, per 100 g and per
/// serving. Where an ingredient does not show a nutrient the total is only a
/// lower bound: it reads "At least ...", carries the grey incomplete marker
/// and is never a plain number (and never green). A missing value reads
/// "Not known". A nutrient the member hides is not drawn at all.
class RecipeNutrients extends StatelessWidget {
  const RecipeNutrients({super.key, required this.recipe});

  final RecipeOut recipe;

  static const per100Key = Key('recipe-per-100g');
  static const perServingKey = Key('recipe-per-serving');
  static const noteKey = Key('recipe-incomplete-note');
  static Key rowKey(String scope, String nutrient) =>
      Key('recipe-$scope-$nutrient');
  static Key markerKey(String scope, String nutrient) =>
      Key('recipe-$scope-$nutrient-incomplete');

  @override
  Widget build(BuildContext context) {
    final hidden = recipe.numbersHidden;
    final shown = [
      for (final k in _rows)
        if (!(k == 'energy_kcal' ? hidden.energy : hidden.macros)) k,
    ];
    if (shown.isEmpty) return const SizedBox.shrink();
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final partial = shown.any(recipe.incompleteNutrients.contains);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _block(
          context,
          'per-100g',
          per100Key,
          l10n.recipesPer100g,
          recipe.per100g,
          shown,
        ),
        if (recipe.perServing != null) ...[
          const SizedBox(height: SnTokens.space3),
          _block(
            context,
            'per-serving',
            perServingKey,
            l10n.recipesPerServing,
            recipe.perServing!,
            shown,
          ),
        ],
        if (partial)
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Text(
              l10n.recipesIncomplete,
              key: noteKey,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
      ],
    );
  }

  Widget _block(
    BuildContext context,
    String scope,
    Key key,
    String title,
    NutrientSnapshot values,
    List<String> shown,
  ) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    String label(String k) => switch (k) {
      'energy_kcal' => l10n.confirmFieldEnergyKcal,
      'protein_g' => l10n.confirmFieldProteinG,
      'carbs_g' => l10n.confirmFieldCarbsG,
      'sugars_g' => l10n.confirmFieldSugarsG,
      'fat_g' => l10n.confirmFieldFatG,
      'sat_fat_g' => l10n.confirmFieldSatFatG,
      'fibre_g' => l10n.confirmFieldFiberG,
      _ => l10n.confirmFieldSaltG,
    };
    return Column(
      key: key,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(title, style: theme.textTheme.titleSmall),
        for (final k in shown)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
            child: Row(
              key: rowKey(scope, k),
              children: [
                Expanded(
                  child: Text(label(k), style: theme.textTheme.bodyMedium),
                ),
                ..._cell(l10n, theme, c, scope, k, _value(values, k)),
              ],
            ),
          ),
      ],
    );
  }

  List<Widget> _cell(
    AppLocalizations l10n,
    ThemeData theme,
    SnColors c,
    String scope,
    String k,
    num? v,
  ) {
    final incomplete = recipe.incompleteNutrients.contains(k);
    final marker = incomplete
        ? Padding(
            padding: const EdgeInsetsDirectional.only(start: SnTokens.space1),
            child: Icon(
              Icons.info_outline_rounded,
              key: markerKey(scope, k),
              size: SnTokens.fontSizeMd,
              color: c.textSecondary,
              semanticLabel: l10n.recipesIncomplete,
            ),
          )
        : null;
    if (v == null) {
      return [
        Text(
          l10n.foodsNotKnown,
          style: theme.textTheme.bodySmall?.copyWith(
            color: c.textSecondary,
            fontStyle: FontStyle.italic,
          ),
        ),
        ?marker,
      ];
    }
    final text = k == 'energy_kcal'
        ? l10n.targetsKcalValue(formatForDisplay(v))
        : l10n.targetsGValue(formatForDisplay(v));
    return [
      Text(
        incomplete ? l10n.diaryWeekAtLeast(text) : text,
        // A lower bound is grey, never the colour of a complete value.
        style: incomplete
            ? theme.textTheme.bodyMedium?.copyWith(color: c.textSecondary)
            : theme.textTheme.bodyMedium,
      ),
      ?marker,
    ];
  }
}
