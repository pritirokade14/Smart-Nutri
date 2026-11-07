import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
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
import '../../diary/domain/slot_label.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../meals/data/meals_repository.dart';
import '../../scan/domain/number_text.dart';
import '../data/foods_repository.dart';
import '../domain/portion_preview.dart';
import '../domain/unit_label.dart';
import 'foods_providers.dart';

/// What the user chose in the picker. The caller builds the diary log from
/// it; the API converts the unit.
typedef PortionChoice = ({
  FoodRef food,
  String name,
  num quantity,
  String unit,
  String? slotId,
});

/// Opens the portion picker for [food]. [onSave] logs the choice (online or
/// queued) and may throw [MealsFailure]; the picker shows its message and
/// stays open. Returns what [onSave] returned, or null when closed.
Future<MealLogResult?> showPortionPicker(
  BuildContext context, {
  required FoodRef food,
  required String name,
  required String memberId,
  String? slotId,
  required Future<MealLogResult> Function(PortionChoice choice) onSave,
}) => showModalBottomSheet<MealLogResult>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => PortionPickerSheet(
    food: food,
    name: name,
    memberId: memberId,
    slotId: slotId,
    onSave: onSave,
  ),
);

/// The nutrient keys of the preview, in display order.
const _previewKeys = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'fat_g',
  'sugars_g',
];

class PortionPickerSheet extends ConsumerStatefulWidget {
  const PortionPickerSheet({
    super.key,
    required this.food,
    required this.name,
    required this.memberId,
    required this.onSave,
    this.slotId,
  });

  final FoodRef food;
  final String name;
  final String memberId;
  final String? slotId;
  final Future<MealLogResult> Function(PortionChoice choice) onSave;

  static Key unitKey(String code) => Key('portion-unit-$code');
  static Key fractionKey(String label) => Key('portion-fraction-$label');
  static Key slotKey(String id) => Key('portion-slot-$id');
  static Key setGramsKey(String code) => Key('portion-set-grams-$code');
  static Key previewKey(String nutrient) => Key('portion-preview-$nutrient');
  static const quantityKey = Key('portion-quantity');
  static const minusKey = Key('portion-minus');
  static const plusKey = Key('portion-plus');
  static const gramsHintKey = Key('portion-grams-hint');
  static const editGramsKey = Key('portion-edit-grams');
  static const resetGramsKey = Key('portion-reset-grams');
  static const gramsInputKey = Key('portion-grams-input');
  static const gramsConfirmKey = Key('portion-grams-confirm');
  static const previewKeyAll = Key('portion-preview');
  static const previewNoteKey = Key('portion-preview-note');
  static const ingredientsKey = Key('portion-dish-ingredients');
  static const reviewKey = Key('portion-review-pending');
  static const saveKey = Key('portion-save');

  /// The quick fractions, as typed.
  static const fractions = {'¼': 0.25, '½': 0.5, '1': 1.0, '1½': 1.5, '2': 2.0};

  @override
  ConsumerState<PortionPickerSheet> createState() => _PortionPickerSheetState();
}

class _PortionPickerSheetState extends ConsumerState<PortionPickerSheet> {
  final _quantity = TextEditingController(text: '1');
  String? _unit;
  String? _slot;
  bool _busy = false;
  String? _error;

  FoodDetailKey get _key => (food: widget.food, memberId: widget.memberId);

  @override
  void dispose() {
    _quantity.dispose();
    super.dispose();
  }

  num? get _quantityValue {
    final p = parseNumber(_quantity.text);
    final v = p.value;
    return p.ok && v != null && v > 0 ? v : null;
  }

  /// The selected unit if the API still resolves it, else its default.
  FoodUnitOut? _selected(FoodDetailOut d) {
    for (final u in d.units) {
      if (u.code == (_unit ?? d.defaultUnit)) return u;
    }
    for (final u in d.units) {
      if (u.code == d.defaultUnit) return u;
    }
    return d.units.firstOrNull;
  }

  void _setQuantity(num v) => setState(() {
    _quantity.text = formatForDisplay(v);
  });

  void _bump(FoodUnitOut unit, int direction) {
    final step = unit.code == 'g' || unit.code == 'ml' ? 10 : 0.5;
    final v = (_quantityValue ?? 0) + direction * step;
    if (v > 0) _setQuantity(v);
  }

  Future<void> _run(Future<void> Function() call) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await call();
      if (mounted) setState(() => _busy = false);
    } on FoodsFailure catch (e) {
      _fail(e.code);
    } on MealsFailure catch (e) {
      _fail(e.code);
    }
  }

  void _fail(String? code) {
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = localizedErrorCode(AppLocalizations.of(context), code);
    });
  }

  /// Asks for grams (or ml) for one [code], saves it and reloads the food.
  Future<void> _editGrams(FoodDetailOut d, String code, {num? initial}) async {
    final value = await showDialog<num>(
      context: context,
      builder: (_) => _GramsDialog(
        unit: unitLabel(AppLocalizations.of(context), code, 1),
        initial: initial,
        ml: d.basis == FoodDetailOutBasis.ml,
      ),
    );
    if (value == null || !mounted) return;
    await _run(() async {
      await ref
          .read(foodsRepositoryProvider)
          .putPortion(widget.food, code, value, memberId: widget.memberId);
      setState(() => _unit = code);
      ref.invalidate(foodDetailProvider(_key));
      await ref.read(foodDetailProvider(_key).future);
    });
  }

  Future<void> _resetGrams(String code) => _run(() async {
    await ref.read(foodsRepositoryProvider).deletePortion(widget.food, code);
    ref.invalidate(foodDetailProvider(_key));
    await ref.read(foodDetailProvider(_key).future);
  });

  Future<void> _save(FoodUnitOut unit, String? slotId) => _run(() async {
    final result = await widget.onSave((
      food: widget.food,
      name: widget.name,
      quantity: _quantityValue!,
      unit: unit.code,
      slotId: slotId,
    ));
    if (mounted) Navigator.of(context).pop(result);
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final detail = ref.watch(foodDetailProvider(_key));
    final d = detail.value;
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
            Text(widget.name, style: theme.textTheme.titleLarge),
            const SizedBox(height: SnTokens.space1),
            Text(l10n.foodsPortionTitle, style: theme.textTheme.titleSmall),
            const SizedBox(height: SnTokens.space3),
            if (d == null && detail.hasError)
              ErrorState(
                message: localizedErrorCode(
                  l10n,
                  detail.error is FoodsFailure
                      ? (detail.error! as FoodsFailure).code
                      : apiErrorCode(detail.error!),
                ),
                onRetry: () => ref.invalidate(foodDetailProvider(_key)),
              )
            else if (d == null)
              const LoadingSkeleton(lines: 4)
            else
              ..._body(context, d),
          ],
        ),
      ),
    );
  }

  List<Widget> _body(BuildContext context, FoodDetailOut d) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final unit = _selected(d);
    final qty = _quantityValue;
    final slots = ref.watch(mealSlotsProvider).value;
    final slotId = _slot ?? widget.slotId ?? slots?.suggestedSlotId;
    final error = _error;
    final count = qty ?? 1;
    final editable =
        unit != null && !const {'g', 'ml', 'serving'}.contains(unit.code);
    return [
      if (unit == null)
        // Nothing resolves: never offer a unit the API cannot convert.
        Text(l10n.errorUnitGramsUnknown, style: theme.textTheme.bodyMedium)
      else ...[
        Wrap(
          spacing: SnTokens.space2,
          runSpacing: SnTokens.space2,
          children: [
            for (final u in d.units)
              ChoiceChip(
                key: PortionPickerSheet.unitKey(u.code),
                label: Text(unitChipLabel(l10n, u.code, count, ml: u.ml)),
                selected: u.code == unit.code,
                onSelected: _busy
                    ? null
                    : (_) => setState(() => _unit = u.code),
              ),
          ],
        ),
        const SizedBox(height: SnTokens.space3),
        Row(
          children: [
            IconButton(
              key: PortionPickerSheet.minusKey,
              icon: const Icon(Icons.remove_circle_outline_rounded),
              onPressed: _busy ? null : () => _bump(unit, -1),
            ),
            Expanded(
              child: TextField(
                key: PortionPickerSheet.quantityKey,
                controller: _quantity,
                enabled: !_busy,
                textAlign: TextAlign.center,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: l10n.foodsPortionQuantity,
                ),
              ),
            ),
            IconButton(
              key: PortionPickerSheet.plusKey,
              icon: const Icon(Icons.add_circle_outline_rounded),
              onPressed: _busy ? null : () => _bump(unit, 1),
            ),
          ],
        ),
        Wrap(
          spacing: SnTokens.space2,
          children: [
            for (final f in PortionPickerSheet.fractions.entries)
              ActionChip(
                key: PortionPickerSheet.fractionKey(f.key),
                label: Text(f.key),
                onPressed: _busy ? null : () => _setQuantity(f.value),
              ),
          ],
        ),
        const SizedBox(height: SnTokens.space2),
        if (unit.code != 'g' && unit.code != 'ml')
          Text(
            key: PortionPickerSheet.gramsHintKey,
            d.basis == FoodDetailOutBasis.ml
                ? l10n.unitAmountHintMl(
                    formatForDisplay(unit.gramsPerUnit),
                    unitLabel(l10n, unit.code, 1),
                  )
                : l10n.unitGramsHint(
                    formatForDisplay(unit.gramsPerUnit),
                    unitLabel(l10n, unit.code, 1),
                  ),
            style: theme.textTheme.bodyMedium,
          ),
        if (unit.userOverride)
          Text(
            l10n.unitYourValue,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        if (editable)
          Wrap(
            children: [
              TextButton(
                key: PortionPickerSheet.editGramsKey,
                onPressed: _busy
                    ? null
                    : () => _editGrams(
                        d,
                        unit.code,
                        initial: unit.userOverride ? unit.gramsPerUnit : null,
                      ),
                child: Text(l10n.unitEditGrams),
              ),
              if (unit.userOverride)
                TextButton(
                  key: PortionPickerSheet.resetGramsKey,
                  onPressed: _busy ? null : () => _resetGrams(unit.code),
                  child: Text(l10n.unitResetGrams),
                ),
            ],
          ),
      ],
      for (final code in d.settableUnits)
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: TextButton(
            key: PortionPickerSheet.setGramsKey(code),
            onPressed: _busy ? null : () => _editGrams(d, code),
            child: Text(l10n.unitSetGrams(unitLabel(l10n, code, 1))),
          ),
        ),
      if (unit != null && qty != null) ..._preview(l10n, d, unit, qty),
      if (d.dish != null && d.dish!.ingredients.isNotEmpty) ...[
        const SizedBox(height: SnTokens.space3),
        Text(l10n.foodsDishIngredients, style: theme.textTheme.titleSmall),
        Column(
          key: PortionPickerSheet.ingredientsKey,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final i in d.dish!.ingredients)
              Text(
                [
                  ?i.name,
                  if (i.grams != null)
                    l10n.diaryGramsLine(formatForDisplay(i.grams!)),
                ].join(' · '),
                style: theme.textTheme.bodySmall,
              ),
          ],
        ),
      ],
      if (d.reviewPending) ...[
        const SizedBox(height: SnTokens.space2),
        Text(
          l10n.foodsReviewPending,
          key: PortionPickerSheet.reviewKey,
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
      ],
      SourceAttribution(
        keys: d.attributions,
        offBarcode: widget.food.kind == FoodKindPath.off
            ? widget.food.id
            : null,
      ),
      if (slots != null) ...[
        const SizedBox(height: SnTokens.space2),
        Wrap(
          spacing: SnTokens.space2,
          runSpacing: SnTokens.space2,
          children: [
            for (final s in slots.items.where((s) => !s.archived))
              ChoiceChip(
                key: PortionPickerSheet.slotKey(s.id),
                label: Text(
                  slotLabel(
                    l10n,
                    labelKey: s.labelKey,
                    customLabel: s.customLabel,
                  ),
                ),
                selected: s.id == slotId,
                onSelected: _busy ? null : (_) => setState(() => _slot = s.id),
              ),
          ],
        ),
      ],
      if (error != null) ...[
        const SizedBox(height: SnTokens.space3),
        InlineErrorBanner(message: error),
      ],
      const SizedBox(height: SnTokens.space3),
      PrimaryButton(
        buttonKey: PortionPickerSheet.saveKey,
        label: l10n.foodsPortionSave,
        icon: Icons.check_rounded,
        busy: _busy,
        onPressed: unit != null && qty != null
            ? () => _save(unit, slotId)
            : null,
      ),
    ];
  }

  /// The live estimate. Nothing is drawn for a nutrient the member hides, and
  /// not at all when everything is hidden. An unknown value says so: never 0.
  List<Widget> _preview(
    AppLocalizations l10n,
    FoodDetailOut d,
    FoodUnitOut unit,
    num qty,
  ) {
    final hidden = d.numbersHidden;
    final shown = [
      for (final k in _previewKeys)
        if (!(k == 'energy_kcal' ? hidden.energy : hidden.macros)) k,
    ];
    if (shown.isEmpty) return const [];
    final per100 = d.per100;
    final values = previewPortion(
      {
        'energy_kcal': per100.energyKcal,
        'protein_g': per100.proteinG,
        'carbs_g': per100.carbsG,
        'fat_g': per100.fatG,
        'sugars_g': per100.sugarsG,
      },
      qty,
      unit.gramsPerUnit,
    );
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    String label(String k) => switch (k) {
      'energy_kcal' => l10n.nutrientEnergyKcal,
      'protein_g' => l10n.nutrientProteinG,
      'carbs_g' => l10n.nutrientCarbsG,
      'fat_g' => l10n.nutrientFatG,
      _ => l10n.nutrientSugarsG,
    };
    return [
      const SizedBox(height: SnTokens.space3),
      Column(
        key: PortionPickerSheet.previewKeyAll,
        children: [
          for (final k in shown)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
              child: Row(
                key: PortionPickerSheet.previewKey(k),
                children: [
                  Expanded(
                    child: Text(label(k), style: theme.textTheme.bodyMedium),
                  ),
                  if (values[k] == null)
                    Text(
                      l10n.foodsNotKnown,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: c.textSecondary,
                        fontStyle: FontStyle.italic,
                      ),
                    )
                  else
                    Text(
                      k == 'energy_kcal'
                          ? l10n.targetsKcalValue(values[k]!)
                          : l10n.targetsGValue(values[k]!),
                      style: theme.textTheme.bodyMedium,
                    ),
                ],
              ),
            ),
          Text(
            l10n.foodsPreviewNote,
            key: PortionPickerSheet.previewNoteKey,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        ],
      ),
    ];
  }
}

/// Asks for the grams (or ml) of one unit. Returns a number above 0 and up
/// to 2000, else null.
class _GramsDialog extends StatefulWidget {
  const _GramsDialog({required this.unit, required this.ml, this.initial});

  final String unit;
  final bool ml;
  final num? initial;

  @override
  State<_GramsDialog> createState() => _GramsDialogState();
}

class _GramsDialogState extends State<_GramsDialog> {
  late final _c = TextEditingController(
    text: widget.initial == null ? '' : formatForDisplay(widget.initial!),
  );

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  num? get _value {
    final p = parseNumber(_c.text);
    final v = p.value;
    return p.ok && v != null && v > 0 && v <= 2000 ? v : null;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    return AlertDialog(
      title: Text(l10n.unitSetGrams(widget.unit)),
      content: TextField(
        key: PortionPickerSheet.gramsInputKey,
        controller: _c,
        autofocus: true,
        onChanged: (_) => setState(() {}),
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: l10n.unitYourValue,
          suffixText: widget.ml ? l10n.unitMl(1) : l10n.unitG(1),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(material.cancelButtonLabel),
        ),
        TextButton(
          key: PortionPickerSheet.gramsConfirmKey,
          onPressed: _value == null
              ? null
              : () => Navigator.of(context).pop(_value),
          child: Text(material.okButtonLabel),
        ),
      ],
    );
  }
}
