import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import 'package:uuid/uuid.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../scan/domain/number_text.dart';
import '../data/foods_repository.dart';
import '../domain/unit_label.dart';
import 'foods_providers.dart';
import 'my_foods_providers.dart';

/// The nutrient fields in display order: the key of `CustomNutrientsIn`.
const customFoodNutrientKeys = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'sugars_g',
  'fat_g',
  'sat_fat_g',
  'fibre_g',
  'salt_g',
  'sodium_mg',
];

String _nutrientLabel(AppLocalizations l10n, String key) => switch (key) {
  'energy_kcal' => l10n.confirmFieldEnergyKcal,
  'protein_g' => l10n.confirmFieldProteinG,
  'carbs_g' => l10n.confirmFieldCarbsG,
  'sugars_g' => l10n.customFoodFieldSugars,
  'fat_g' => l10n.confirmFieldFatG,
  'sat_fat_g' => l10n.customFoodFieldSatFat,
  'fibre_g' => l10n.confirmFieldFiberG,
  'salt_g' => l10n.customFoodFieldSalt,
  _ => l10n.customFoodFieldSodium,
};

/// The create and edit screen for one custom food. Online only: the API
/// checks the values and works out the per-100 numbers. Blank is sent as
/// absent (unknown), never as 0.
class CustomFoodFormScreen extends ConsumerStatefulWidget {
  const CustomFoodFormScreen({super.key, this.food, this.foodId});

  /// The food being edited, when the caller has it.
  final CustomFoodOut? food;

  /// The food's id for a deep link (the list is searched for it).
  final String? foodId;

  static const nameKey = Key('custom-food-name');
  static const brandKey = Key('custom-food-brand');
  static const basisKey = Key('custom-food-basis');
  static const valuesPerKey = Key('custom-food-values-per');
  static const servingKey = Key('custom-food-serving');
  static const densityKey = Key('custom-food-density');
  static const barcodeKey = Key('custom-food-barcode');
  static const addPortionKey = Key('custom-food-add-portion');
  static const saveKey = Key('custom-food-save');
  static const deleteKey = Key('custom-food-delete');
  static const deleteConfirmKey = Key('custom-food-delete-confirm');
  static const historyKeptKey = Key('custom-food-history-kept');
  static const errorKey = Key('custom-food-error');
  static Key nutrientKey(String k) => Key('custom-food-$k');
  static Key portionUnitKey(int i) => Key('custom-food-portion-unit-$i');
  static Key portionGramsKey(int i) => Key('custom-food-portion-grams-$i');

  @override
  ConsumerState<CustomFoodFormScreen> createState() =>
      _CustomFoodFormScreenState();
}

class _CustomFoodFormScreenState extends ConsumerState<CustomFoodFormScreen> {
  CustomFoodOut? _food;
  bool _resolved = false;

  @override
  void initState() {
    super.initState();
    _food = widget.food;
    _resolved = widget.foodId == null || widget.food != null;
    if (!_resolved) _find();
  }

  /// A deep link has only the id: page through the list for it.
  Future<void> _find() async {
    final repo = ref.read(customFoodsRepositoryProvider);
    String? cursor;
    try {
      do {
        final page = await repo.list(cursor: cursor);
        for (final f in page.items) {
          if (f.id == widget.foodId) {
            if (mounted) setState(() => _food = f);
            break;
          }
        }
        cursor = _food == null ? page.nextCursor : null;
      } while (cursor != null);
    } on Object {
      // Falls through to an empty create form.
    }
    if (mounted) setState(() => _resolved = true);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.customFoodTitle)),
      body: _resolved
          ? CustomFoodForm(key: ValueKey(_food?.id), food: _food)
          : const Padding(
              padding: EdgeInsets.all(SnTokens.space4),
              child: LoadingSkeleton(lines: 5),
            ),
    );
  }
}

class _PortionRow {
  _PortionRow(this.unit, String grams)
    : grams = TextEditingController(text: grams);
  String? unit;
  final TextEditingController grams;
}

class CustomFoodForm extends ConsumerStatefulWidget {
  const CustomFoodForm({super.key, this.food});

  final CustomFoodOut? food;

  @override
  ConsumerState<CustomFoodForm> createState() => _CustomFoodFormState();
}

class _CustomFoodFormState extends ConsumerState<CustomFoodForm> {
  late final _name = TextEditingController(text: widget.food?.name ?? '');
  late final _brand = TextEditingController(text: widget.food?.brand ?? '');
  late final _barcode = TextEditingController(text: widget.food?.barcode ?? '');
  late final _serving = TextEditingController(
    text: widget.food?.entered.servingG == null
        ? ''
        : formatForDisplay(widget.food!.entered.servingG!),
  );
  late final _density = TextEditingController(
    text: widget.food?.densityGPerMl == null
        ? ''
        : formatForDisplay(widget.food!.densityGPerMl!),
  );
  late final Map<String, TextEditingController> _nutrients = {
    for (final k in customFoodNutrientKeys)
      k: TextEditingController(text: _entered(k)),
  };
  late final _portions = <_PortionRow>[
    for (final p in widget.food?.portions ?? const <CustomPortionOut>[])
      _PortionRow(p.unit, formatForDisplay(p.gramsPerUnit)),
  ];
  late CustomFoodInBasis _basis = widget.food?.basis == CustomFoodOutBasis.ml
      ? CustomFoodInBasis.ml
      : CustomFoodInBasis.g;
  late CustomFoodInValuesPer _per =
      widget.food?.entered.valuesPer == EnteredOutValuesPer.serving
      ? CustomFoodInValuesPer.serving
      : CustomFoodInValuesPer.value100;

  /// The clientId of this form: a retried create never stores it twice.
  late final String _clientId = const Uuid().v4();

  bool _busy = false;
  bool _submitted = false;
  String? _error;
  Set<String> _badFields = {};

  String _entered(String key) {
    final n = widget.food?.entered.nutrients;
    final v = switch (key) {
      'energy_kcal' => n?.energyKcal,
      'protein_g' => n?.proteinG,
      'carbs_g' => n?.carbsG,
      'sugars_g' => n?.sugarsG,
      'fat_g' => n?.fatG,
      'sat_fat_g' => n?.satFatG,
      'fibre_g' => n?.fibreG,
      'salt_g' => n?.saltG,
      _ => n?.sodiumMg,
    };
    return v == null ? '' : formatForDisplay(v);
  }

  @override
  void dispose() {
    for (final c in [_name, _brand, _barcode, _serving, _density]) {
      c.dispose();
    }
    for (final c in _nutrients.values) {
      c.dispose();
    }
    for (final p in _portions) {
      p.grams.dispose();
    }
    super.dispose();
  }

  bool get _isEdit => widget.food != null;

  ({bool ok, num? value}) _num(TextEditingController c) => parseNumber(c.text);

  /// Every typed number parses (blank is fine: it stays unknown).
  bool get _numbersOk =>
      _nutrients.values.every((c) => _num(c).ok) &&
      _num(_density).ok &&
      (_per == CustomFoodInValuesPer.value100 ||
          (_num(_serving).ok && (_num(_serving).value ?? 0) > 0)) &&
      _portions.every((p) {
        final v = _num(p.grams);
        return p.unit != null && v.ok && (v.value ?? 0) > 0;
      });

  bool get _canSave => _name.text.trim().isNotEmpty && _numbersOk && !_busy;

  CustomFoodIn _body() {
    num? n(String k) => _num(_nutrients[k]!).value;
    final brand = _brand.text.trim();
    final barcode = _barcode.text.trim();
    final density = _num(_density).value;
    return CustomFoodIn(
      name: _name.text.trim(),
      brand: brand.isEmpty ? null : brand,
      basis: _basis,
      valuesPer: _per,
      servingG: _per == CustomFoodInValuesPer.serving
          ? _num(_serving).value
          : null,
      // A blank field is absent (unknown), never 0.
      nutrients: CustomNutrientsIn(
        energyKcal: n('energy_kcal'),
        proteinG: n('protein_g'),
        carbsG: n('carbs_g'),
        sugarsG: n('sugars_g'),
        fatG: n('fat_g'),
        satFatG: n('sat_fat_g'),
        fibreG: n('fibre_g'),
        saltG: n('salt_g'),
        sodiumMg: n('sodium_mg'),
      ),
      densityGPerMl: _basis == CustomFoodInBasis.ml ? density : null,
      barcode: barcode.isEmpty ? null : barcode,
      portions: _portions.isEmpty
          ? null
          : [
              for (final p in _portions)
                CustomPortionIn(
                  unit: CustomPortionInUnit.fromJson(p.unit!),
                  gramsPerUnit: _num(p.grams).value!,
                ),
            ],
    );
  }

  /// The `details.fields` of an API error, as the nutrient keys it names.
  Set<String> _fieldsOf(Object? cause) {
    if (cause is! DioException) return {};
    final details = parseErrorEnvelope(cause.response?.data)?.error.details;
    final fields = details is Map ? details['fields'] : null;
    if (fields is! List) return {};
    return {for (final f in fields) f.toString().split('.').last};
  }

  Future<void> _save() async {
    setState(() => _submitted = true);
    if (!_canSave) return;
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
      _badFields = {};
    });
    final repo = ref.read(customFoodsRepositoryProvider);
    try {
      final saved = _isEdit
          ? await repo.update(widget.food!.id, _body())
          : await repo.create(_body(), clientId: _clientId);
      ref.invalidate(customFoodsProvider);
      messenger.showSnackBar(SnackBar(content: Text(l10n.customFoodSaved)));
      if (mounted) nav.pop(saved);
    } on FoodsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
        _badFields = _fieldsOf(e.cause);
      });
    }
  }

  Future<void> _delete() async {
    final l10n = AppLocalizations.of(context);
    final nav = Navigator.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.customFoodDeleteConfirm),
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.customFoodHistoryKept,
              key: CustomFoodFormScreen.historyKeptKey,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l10n.commonCancel),
          ),
          TextButton(
            key: CustomFoodFormScreen.deleteConfirmKey,
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l10n.customFoodDelete),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(customFoodsRepositoryProvider).delete(widget.food!.id);
      ref.invalidate(customFoodsProvider);
      if (mounted) nav.pop();
    } on FoodsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
      });
    }
  }

  Widget _numberField(
    Key key,
    TextEditingController c,
    String label, {
    String? suffix,
    bool bad = false,
  }) {
    final l10n = AppLocalizations.of(context);
    final invalid = !_num(c).ok;
    return TextField(
      key: key,
      controller: c,
      enabled: !_busy,
      onChanged: (_) => setState(() {}),
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        suffixText: suffix,
        errorText: invalid
            ? l10n.errorValidationError
            : bad
            ? l10n.errorImplausibleValue
            : null,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final ml = _basis == CustomFoodInBasis.ml;
    final basisUnit = ml ? l10n.unitMl(1) : l10n.unitG(1);
    final units = ref.watch(foodUnitsProvider).value;
    final choices = [
      for (final u in units ?? const <UnitOut>[])
        if (u.kind != UnitOutKind.mass && u.code != 'serving') u.code,
    ];
    const gap = SizedBox(height: SnTokens.space3);
    return ListView(
      padding: const EdgeInsets.all(SnTokens.space4),
      children: [
        TextField(
          key: CustomFoodFormScreen.nameKey,
          controller: _name,
          enabled: !_busy,
          maxLength: 80,
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            labelText: l10n.customFoodName,
            counterText: '',
          ),
        ),
        gap,
        TextField(
          key: CustomFoodFormScreen.brandKey,
          controller: _brand,
          enabled: !_busy,
          decoration: InputDecoration(labelText: l10n.customFoodBrand),
        ),
        gap,
        SegmentedButton<CustomFoodInBasis>(
          key: CustomFoodFormScreen.basisKey,
          segments: [
            ButtonSegment(
              value: CustomFoodInBasis.g,
              label: Text(l10n.customFoodBasisG),
            ),
            ButtonSegment(
              value: CustomFoodInBasis.ml,
              label: Text(l10n.customFoodBasisMl),
            ),
          ],
          selected: {_basis},
          onSelectionChanged: _busy
              ? null
              : (s) => setState(() => _basis = s.single),
        ),
        gap,
        SegmentedButton<CustomFoodInValuesPer>(
          key: CustomFoodFormScreen.valuesPerKey,
          segments: [
            ButtonSegment(
              value: CustomFoodInValuesPer.value100,
              label: Text(
                ml ? l10n.foodsValuesPer100ml : l10n.foodsValuesPer100g,
              ),
            ),
            ButtonSegment(
              value: CustomFoodInValuesPer.serving,
              label: Text(l10n.foodsValuesPerServing),
            ),
          ],
          selected: {_per},
          onSelectionChanged: _busy
              ? null
              : (s) => setState(() => _per = s.single),
        ),
        if (_per == CustomFoodInValuesPer.serving) ...[
          gap,
          _numberField(
            CustomFoodFormScreen.servingKey,
            _serving,
            l10n.customFoodServingSize,
            suffix: basisUnit,
          ),
        ],
        gap,
        Text(
          l10n.foodsBlankIsUnknown,
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
        for (final k in customFoodNutrientKeys) ...[
          const SizedBox(height: SnTokens.space2),
          _numberField(
            CustomFoodFormScreen.nutrientKey(k),
            _nutrients[k]!,
            _nutrientLabel(l10n, k),
            bad: _badFields.contains(k),
          ),
        ],
        if (ml) ...[
          gap,
          _numberField(
            CustomFoodFormScreen.densityKey,
            _density,
            l10n.customFoodDensity,
            bad: _badFields.contains('density_g_per_ml'),
          ),
          Text(
            l10n.customFoodDensityHint,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        ],
        gap,
        TextField(
          key: CustomFoodFormScreen.barcodeKey,
          controller: _barcode,
          enabled: !_busy,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: l10n.customFoodBarcode),
        ),
        if (choices.isNotEmpty) ...[
          gap,
          Text(l10n.customFoodPortions, style: theme.textTheme.titleSmall),
          for (var i = 0; i < _portions.length; i++)
            _portionRow(l10n, i, choices, basisUnit),
          if (_portions.length < 10)
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                key: CustomFoodFormScreen.addPortionKey,
                onPressed: _busy
                    ? null
                    : () => setState(() {
                        final used = {for (final p in _portions) p.unit};
                        final free = choices.where((u) => !used.contains(u));
                        if (free.isNotEmpty) {
                          _portions.add(_PortionRow(free.first, ''));
                        }
                      }),
                icon: const Icon(Icons.add_rounded),
                label: Text(l10n.customFoodPortions),
              ),
            ),
        ],
        if (_error != null) ...[
          gap,
          InlineErrorBanner(
            key: CustomFoodFormScreen.errorKey,
            message: _error!,
          ),
        ],
        gap,
        PrimaryButton(
          buttonKey: CustomFoodFormScreen.saveKey,
          label: l10n.customFoodSave,
          icon: Icons.check_rounded,
          busy: _busy,
          onPressed: _submitted && !_canSave && !_busy ? null : _save,
        ),
        if (_isEdit) ...[
          gap,
          OutlinedButton.icon(
            key: CustomFoodFormScreen.deleteKey,
            onPressed: _busy ? null : _delete,
            icon: const Icon(Icons.delete_outline_rounded),
            label: Text(l10n.customFoodDelete),
          ),
        ],
      ],
    );
  }

  Widget _portionRow(
    AppLocalizations l10n,
    int i,
    List<String> choices,
    String basisUnit,
  ) {
    final row = _portions[i];
    final used = {
      for (final p in _portions)
        if (p != row) p.unit,
    };
    final options = {
      for (final u in choices)
        if (!used.contains(u)) u,
      ?row.unit,
    }.toList();
    return Row(
      children: [
        Expanded(
          child: DropdownButton<String>(
            key: CustomFoodFormScreen.portionUnitKey(i),
            isExpanded: true,
            value: row.unit,
            items: [
              for (final u in options)
                DropdownMenuItem(value: u, child: Text(unitLabel(l10n, u, 1))),
            ],
            onChanged: _busy ? null : (v) => setState(() => row.unit = v),
          ),
        ),
        const SizedBox(width: SnTokens.space2),
        Expanded(
          child: _numberField(
            CustomFoodFormScreen.portionGramsKey(i),
            row.grams,
            basisUnit,
          ),
        ),
        IconButton(
          icon: const Icon(Icons.close_rounded),
          tooltip: l10n.commonClose,
          onPressed: _busy
              ? null
              : () => setState(() => _portions.removeAt(i).grams.dispose()),
        ),
      ],
    );
  }
}
