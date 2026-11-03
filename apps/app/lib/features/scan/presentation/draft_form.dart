import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/draft_warnings.dart';
import '../domain/number_text.dart';
import 'warning_banner.dart';

/// The editable confirm form for a label draft, or an empty form for manual
/// entry (`draft == null`).
///
/// It transcribes what the pack prints and records the user's explicit
/// choices; it never does nutrient arithmetic and never decides a verdict
/// (Ruling R17). For a scan, every save rule comes from the server's
/// `draft.confirm` hints (Ruling R21); nothing is inferred from `warnings`,
/// `engine_withheld`, `derived_from_serving` or `basis_mismatch`:
/// - offered bases are the non-null `confirm.columns`; a lone one is selected,
///   and of two, per 100 g is preselected (R22);
/// - `basis_required` / `category_required` preselect nothing;
/// - the shown values are the printed column of the chosen basis, else the
///   `shared` printed column; server-derived values are never shown;
/// - a box, unticked, for each of the chosen column's `confirm_fields`; a
///   field is confirmed only by its tick or by an edit;
/// - a mg/g picker when the column says `sodium_unit_required`.
/// Blanks stay blank and are sent as null, never 0.
class DraftForm extends StatefulWidget {
  const DraftForm({
    super.key,
    required this.draft,
    required this.onSave,
    this.scanId,
    this.barcode,
    this.fieldErrors = const {},
    this.saving = false,
    this.header = const [],
    this.footer = const [],
  });

  /// The scan draft, or null for an empty manual-entry form.
  final ProductDraft? draft;
  final void Function(ProductCreate body) onSave;

  /// The label scan the draft came from; sent only with a draft.
  final String? scanId;
  final String? barcode;

  /// Errors from the save request, by field, shown next to the field.
  final Map<String, String> fieldErrors;
  final bool saving;
  final List<Widget> header;
  final List<Widget> footer;

  @override
  State<DraftForm> createState() => DraftFormState();
}

/// One numeric input, showing the exact printed value. Unedited, it sends
/// [original] unchanged; edited, it sends what the user typed.
class _NumInput {
  _NumInput(this.original)
    : initialText = original == null ? '' : formatForDisplay(original),
      controller = TextEditingController(
        text: original == null ? '' : formatForDisplay(original),
      );

  final num? original;
  final String initialText;
  final TextEditingController controller;

  /// R24: the value differs from the draft's. Typing the same number, or
  /// editing and then changing back, is not an edit (nothing is confirmed).
  bool get edited {
    if (controller.text == initialText) return false;
    final parsed = parseNumber(controller.text);
    return !(parsed.ok && parsed.value == original);
  }

  bool get valid => !edited || parseNumber(controller.text).ok;
  num? get value => edited ? parseNumber(controller.text).value : original;
  bool get isBlank => controller.text.trim().isEmpty;
}

num? _nutrient(DraftNutrients? n, String f) => switch (f) {
  'energy_kcal' => n?.energyKcal,
  'protein_g' => n?.proteinG,
  'carbs_g' => n?.carbsG,
  'sugars_g' => n?.sugarsG,
  'added_sugars_g' => n?.addedSugarsG,
  'fat_g' => n?.fatG,
  'sat_fat_g' => n?.satFatG,
  'trans_fat_g' => n?.transFatG,
  'fiber_g' => n?.fiberG,
  'salt_g' => n?.saltG,
  'sodium_mg' => n?.sodiumMg,
  _ => null,
};

/// The two bases, in contract order.
const _bases = ['per_100g', 'per_serving'];

/// Input columns that are not a printed draft column.
const _manualSource = 'manual';
const _blankSource = 'blank';

const _statementFields = ['allergen_statement', 'may_contain_statement'];

class DraftFormState extends State<DraftForm> {
  late final ProductDraft? _draft = widget.draft;
  late final List<DraftWarning> _warnings = [
    for (final w in _draft?.warnings ?? const <String>[]) DraftWarning.parse(w),
  ];

  bool get _scan => _draft != null;

  /// The server's hint for saving with [basis] (null = not offered).
  ColumnConfirm? _hint(String basis) {
    final columns = _draft?.confirm.columns;
    return basis == 'per_100g' ? columns?.per100g : columns?.perServing;
  }

  /// Bases the user may save with: both for manual entry, else exactly the
  /// non-null hint columns.
  late final List<String> _offered = _scan
      ? [
          for (final b in _bases)
            if (_hint(b) != null) b,
        ]
      : _bases;

  /// The printed column to show whatever basis is picked, if any.
  late final String? _sharedSource = _scan
      ? _bases.where((b) => _hint(b)?.shared ?? false).firstOrNull
      : null;

  /// Input columns by source: a printed draft column (`per_100g` /
  /// `per_serving`), [_manualSource] or [_blankSource]. Only columns the
  /// server marks `printed` are filled from the draft.
  final Map<String, Map<String, _NumInput>> _inputs = {};

  String? _basis;
  ProductCreateCategory? _category;
  ProductCreateSodiumUnit? _sodiumUnit;
  ProductCreateVegMark? _vegMark;

  /// Boxes the user ticked, as `<source>.<field>`.
  final Set<String> _ticked = {};
  bool _servingTicked = false;
  final Set<String> _blankConfirmed = {};

  late final _NumInput _serving = _NumInput(_draft?.servingSizeG);
  late final TextEditingController _name = TextEditingController(
    text: _draft?.name ?? '',
  );
  late final TextEditingController _brand = TextEditingController(
    text: _draft?.brand ?? '',
  );
  late final Map<String, TextEditingController> _statements = {
    'allergen_statement': TextEditingController(
      text: _draft?.allergenStatement ?? '',
    ),
    'may_contain_statement': TextEditingController(
      text: _draft?.mayContainStatement ?? '',
    ),
  };
  late final List<TextEditingController> _ingredients = [
    for (final i in _draft?.ingredients ?? const <String>[])
      TextEditingController(text: i),
  ];

  /// One claim per line, as on the web.
  late final TextEditingController _claims = TextEditingController(
    text: (_draft?.claims ?? const <String>[]).join('\n'),
  );

  @override
  void initState() {
    super.initState();
    final draft = _draft;
    Map<String, _NumInput> column(DraftNutrients? n) => {
      for (final f in formNutrientFields) f: _NumInput(_nutrient(n, f)),
    };
    if (draft == null) {
      _inputs[_manualSource] = column(null);
    } else {
      for (final b in _bases) {
        if (_hint(b)?.printed ?? false) {
          _inputs[b] = column(
            b == 'per_100g' ? draft.per100g : draft.perServing,
          );
        }
      }
      _inputs[_blankSource] = column(null);
      // Forced choice when the basis is in doubt. Otherwise a lone offered
      // basis is the only possible one, and with two offered, per 100 g is
      // preselected and the user can switch (R22).
      if (!draft.confirm.basisRequired) {
        if (_offered.length == 1) {
          _basis = _offered.single;
        } else if (_offered.contains('per_100g')) {
          _basis = 'per_100g';
        }
      }
      if (!draft.confirm.categoryRequired) {
        final c = ProductCreateCategory.fromJson(draft.category.json ?? '');
        _category = c == ProductCreateCategory.$unknown ? null : c;
      }
    }
    final veg = ProductCreateVegMark.fromJson(draft?.vegMark?.json ?? '');
    _vegMark = veg == ProductCreateVegMark.$unknown ? null : veg;

    for (final column in _inputs.values) {
      for (final input in column.values) {
        input.controller.addListener(() => setState(() {}));
      }
    }
    for (final c in [_serving.controller, _name, ..._statements.values]) {
      c.addListener(() => setState(() {}));
    }
  }

  @override
  void dispose() {
    for (final column in _inputs.values) {
      for (final i in column.values) {
        i.controller.dispose();
      }
    }
    for (final c in [
      _serving.controller,
      _name,
      _brand,
      ..._statements.values,
      ..._ingredients,
      _claims,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  // --- derived state (from draft.confirm only) ----------------------------

  /// The input column on screen (packages/test-fixtures README, step 2): the
  /// chosen basis's column if printed, else the shared printed column; with
  /// no basis yet, the shared column, else the first printed one; else blank.
  String get _source {
    if (!_scan) return _manualSource;
    final basis = _basis;
    if (basis != null && _inputs.containsKey(basis)) return basis;
    if (_sharedSource case final shared?) return shared;
    if (basis == null) {
      for (final b in _bases) {
        if (_inputs.containsKey(b)) return b;
      }
    }
    return _blankSource;
  }

  Map<String, _NumInput> get _shown => _inputs[_source]!;

  /// The shown numbers are the one printed column, saved as the chosen basis.
  bool get _sharedShown => _sharedSource != null && _source == _sharedSource;

  ColumnConfirm? get _selectedHint =>
      _scan && _basis != null ? _hint(_basis!) : null;

  /// The chosen column's `confirm_fields`.
  Set<String> get _confirmFields => {
    for (final f in _selectedHint?.confirmFields ?? const []) ?f.json,
  };

  bool get _sodiumUnitRequired {
    if (!_scan) return false;
    if (_selectedHint case final hint?) return hint.sodiumUnitRequired;
    return _offered.any((b) => _hint(b)?.sodiumUnitRequired ?? false);
  }

  bool get _unitPickerShown =>
      _sodiumUnitRequired && !_shown['sodium_mg']!.isBlank;

  bool _isConfirmed(String field) =>
      _ticked.contains('$_source.$field') || _shown[field]!.edited;

  bool get _servingConfirmed => _servingTicked || _serving.edited;

  /// The server's hint (R23): the chosen column stores nutrients only with a
  /// confirmed serving size, so Save stays disabled until it is.
  bool get _servingTickRequired =>
      _scan && (_selectedHint?.servingRequired ?? false) && !_servingConfirmed;

  bool _blankNeedsConfirm(String field) {
    final original = field == 'allergen_statement'
        ? _draft?.allergenStatement
        : _draft?.mayContainStatement;
    return (original?.trim().isNotEmpty ?? false) &&
        _statements[field]!.text.trim().isEmpty;
  }

  Set<String> get _invalidFields => {
    for (final e in _shown.entries)
      if (!e.value.valid) e.key,
    if (!_serving.valid) 'serving_size_g',
  };

  Set<String> get _highlighted {
    final out = {...highlightedFields(_warnings), ...widget.fieldErrors.keys};
    if (out.contains('sodium_unit')) out.add('sodium_mg');
    return out..addAll(_invalidFields);
  }

  bool get _canSave =>
      _name.text.trim().isNotEmpty &&
      _category != null &&
      _basis != null &&
      !(_unitPickerShown && _sodiumUnit == null) &&
      !_servingTickRequired &&
      !(_basis == 'per_serving' && _serving.value == null) &&
      _invalidFields.isEmpty &&
      _statementFields.every(
        (f) => !_blankNeedsConfirm(f) || _blankConfirmed.contains(f),
      );

  // --- body ---------------------------------------------------------------

  /// The body Save would send now, or null while basis or category is
  /// unchosen. For tests that assert the body of a save the form blocks.
  @visibleForTesting
  ProductCreate? get previewBody =>
      _basis == null || _category == null ? null : _body();

  ProductCreate _body() {
    final col = _shown;
    num? v(String f) => col[f]!.value;
    String? text(TextEditingController c) =>
        c.text.trim().isEmpty ? null : c.text;
    final fields = _confirmFields;
    final confirmed = <ProductCreateConfirmedFields>[
      if (_scan) ...[
        for (final f in engineFields)
          if (fields.contains(f) && _isConfirmed(f))
            ProductCreateConfirmedFields.fromJson(f),
        // Editing the serving size confirms it, even one the draft lacked.
        if ((fields.contains('serving_size_g') && _servingTicked) ||
            _serving.edited)
          ProductCreateConfirmedFields.servingSizeG,
      ],
    ];
    return ProductCreate(
      scanId: _scan ? widget.scanId : null,
      barcode: widget.barcode,
      name: _name.text.trim(),
      brand: text(_brand)?.trim(),
      category: _category!,
      basis: ProductCreateBasis.fromJson(_basis!),
      nutrients: PrintedNutrients(
        energyKcal: v('energy_kcal'),
        proteinG: v('protein_g'),
        carbsG: v('carbs_g'),
        sugarsG: v('sugars_g'),
        addedSugarsG: v('added_sugars_g'),
        fatG: v('fat_g'),
        satFatG: v('sat_fat_g'),
        transFatG: v('trans_fat_g'),
        fiberG: v('fiber_g'),
        saltG: v('salt_g'),
        sodiumMg: v('sodium_mg'),
      ),
      // Null means mg; only the user's explicit pick is ever sent.
      sodiumUnit: _unitPickerShown ? _sodiumUnit : null,
      servingSizeG: _serving.value,
      ingredients: [
        for (final c in _ingredients)
          if (c.text.trim().isNotEmpty) c.text,
      ],
      allergenStatement: text(_statements['allergen_statement']!),
      mayContainStatement: text(_statements['may_contain_statement']!),
      claims: [
        for (final line in _claims.text.split('\n'))
          if (line.trim().isNotEmpty) line,
      ],
      vegMark: _vegMark,
      confirmedFields: confirmed,
    );
  }

  // --- widgets ------------------------------------------------------------

  Widget _highlight(String field, Widget child) {
    final on = _highlighted.contains(field);
    return Container(
      key: on ? ValueKey('highlight:$field') : null,
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      padding: on ? const EdgeInsets.all(SnTokens.space1) : EdgeInsets.zero,
      decoration: on
          ? BoxDecoration(
              border: Border.all(color: SnTokens.verdictCaution, width: 2),
              borderRadius: BorderRadius.circular(SnTokens.radiusMd),
            )
          : null,
      child: child,
    );
  }

  Widget _required(AppLocalizations l10n, bool missing) => missing
      ? Padding(
          padding: const EdgeInsets.only(top: SnTokens.space1),
          child: Text(
            l10n.confirmChooseRequired,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: SnTokens.verdictCaution,
              fontWeight: FontWeight.w600,
            ),
          ),
        )
      : const SizedBox.shrink();

  Widget _chips<T>({
    String? title,
    required String keyPrefix,
    required List<(T?, String, String)> options,
    required T? selected,
    required ValueChanged<T?> onSelected,
    bool requiredChoice = false,
  }) {
    final l10n = AppLocalizations.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null) ...[
            Text(title, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: SnTokens.space1),
          ],
          Wrap(
            spacing: SnTokens.space2,
            runSpacing: SnTokens.space1,
            children: [
              for (final (value, id, label) in options)
                ChoiceChip(
                  key: ValueKey('$keyPrefix:$id'),
                  label: Text(label),
                  selected: selected == value,
                  onSelected: (_) => setState(() => onSelected(value)),
                ),
            ],
          ),
          if (requiredChoice) _required(l10n, selected == null),
        ],
      ),
    );
  }

  Widget _confirmBox(String key, bool value, ValueChanged<bool> onChanged) {
    final l10n = AppLocalizations.of(context);
    return CheckboxListTile(
      key: ValueKey(key),
      value: value,
      dense: true,
      contentPadding: EdgeInsets.zero,
      controlAffinity: ListTileControlAffinity.leading,
      title: Text(l10n.confirmConfirmValue),
      onChanged: (v) => setState(() => onChanged(v ?? false)),
    );
  }

  Widget _numberField(String field, _NumInput input, {Widget? suffix}) {
    final l10n = AppLocalizations.of(context);
    final label = field == 'sodium_mg' && _unitPickerShown
        ? l10n.confirmSodium
        : fieldLabel(l10n, field) ?? field;
    final needsConfirm = _scan && _confirmFields.contains(field);
    final tickKey = '$_source.$field';
    return _highlight(
      field,
      Column(
        key: ValueKey('field:$field'),
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: input.controller,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: label,
              border: const OutlineInputBorder(),
              errorText:
                  widget.fieldErrors[field] ??
                  (field == 'sodium_mg'
                      ? widget.fieldErrors['sodium_unit']
                      : null) ??
                  (input.valid ? null : l10n.errorValidationError),
              suffixIcon: suffix,
            ),
          ),
          if (needsConfirm) ...[
            Padding(
              padding: const EdgeInsets.only(top: SnTokens.space1),
              child: Text(
                l10n.confirmWithheldHint,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            _confirmBox(
              'confirm:$field',
              _isConfirmed(field),
              (v) => v ? _ticked.add(tickKey) : _ticked.remove(tickKey),
            ),
          ],
        ],
      ),
    );
  }

  /// The picked sodium unit beside the input, shown only with the picker
  /// (otherwise the label already says mg).
  Widget _sodiumSuffix(AppLocalizations l10n) {
    final unit = switch (_sodiumUnit) {
      ProductCreateSodiumUnit.g => l10n.confirmSodiumUnitOptionG,
      ProductCreateSodiumUnit.mg => l10n.confirmSodiumUnitOptionMg,
      _ =>
        '${l10n.confirmSodiumUnitOptionMg} / '
            '${l10n.confirmSodiumUnitOptionG}',
    };
    return Padding(
      key: const ValueKey('sodium_unit_suffix'),
      padding: const EdgeInsets.symmetric(horizontal: SnTokens.space3),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [Text(unit)],
      ),
    );
  }

  Widget _textList({
    required String field,
    required String title,
    required String addLabel,
    required String removeLabel,
    required List<TextEditingController> items,
    required String itemKey,
  }) {
    final error = widget.fieldErrors[field];
    return _highlight(
      field,
      Column(
        key: ValueKey('list:$field'),
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          if (error != null)
            Padding(
              padding: const EdgeInsets.only(top: SnTokens.space1),
              child: Text(
                error,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.error,
                ),
              ),
            ),
          const SizedBox(height: SnTokens.space1),
          for (final (i, c) in items.indexed)
            Padding(
              key: ValueKey('field:$itemKey:$i'),
              padding: const EdgeInsets.only(bottom: SnTokens.space1),
              child: TextField(
                controller: c,
                decoration: InputDecoration(
                  border: const OutlineInputBorder(),
                  isDense: true,
                  // Removing is always the user's own action: items are
                  // never dropped automatically.
                  suffixIcon: IconButton(
                    key: ValueKey('remove:$itemKey:$i'),
                    tooltip: removeLabel,
                    icon: const Icon(Icons.close),
                    onPressed: () {
                      final removed = items.removeAt(i);
                      setState(() {});
                      // The field still holds it until the next frame.
                      WidgetsBinding.instance.addPostFrameCallback(
                        (_) => removed.dispose(),
                      );
                    },
                  ),
                ),
              ),
            ),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton.icon(
              onPressed: () =>
                  setState(() => items.add(TextEditingController())),
              icon: const Icon(Icons.add),
              label: Text(addLabel),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statement(AppLocalizations l10n, String field, String label) {
    final needsConfirm = _blankNeedsConfirm(field);
    return _highlight(
      field,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            key: ValueKey('field:$field'),
            controller: _statements[field],
            minLines: 2,
            maxLines: null,
            decoration: InputDecoration(
              labelText: label,
              border: const OutlineInputBorder(),
              errorText: widget.fieldErrors[field],
            ),
          ),
          if (needsConfirm)
            CheckboxListTile(
              key: ValueKey('blank:$field'),
              value: _blankConfirmed.contains(field),
              dense: true,
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: Text(l10n.confirmClearStatementConfirm),
              onChanged: (v) => setState(
                () => (v ?? false)
                    ? _blankConfirmed.add(field)
                    : _blankConfirmed.remove(field),
              ),
            ),
        ],
      ),
    );
  }

  Widget _plainField(String field, String label, TextEditingController c) =>
      _highlight(
        field,
        TextField(
          key: ValueKey('field:$field'),
          controller: c,
          decoration: InputDecoration(
            labelText: label,
            border: const OutlineInputBorder(),
            errorText: widget.fieldErrors[field],
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final serving = _serving.value;
    final servingBox = _scan && _confirmFields.contains('serving_size_g');
    return SingleChildScrollView(
      padding: const EdgeInsets.all(SnTokens.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ...widget.header,
          for (final w in _warnings) WarningBanner(warning: w),
          const SizedBox(height: SnTokens.space2),
          _plainField('name', l10n.confirmName, _name),
          _plainField('brand', l10n.confirmBrand, _brand),
          const SizedBox(height: SnTokens.space2),
          _highlight(
            'category',
            _chips<ProductCreateCategory>(
              title: l10n.confirmCategory,
              keyPrefix: 'category',
              requiredChoice: true,
              selected: _category,
              onSelected: (v) => _category = v,
              options: [
                for (final c in ProductCreateCategory.$valuesDefined)
                  (c, c.json!, _categoryLabel(l10n, c)),
              ],
            ),
          ),
          _highlight(
            'basis',
            _chips<String>(
              title: l10n.confirmBasis,
              keyPrefix: 'basis',
              requiredChoice: true,
              selected: _basis,
              onSelected: (v) {
                // The picked unit belongs to the column it was picked for.
                final before = _source;
                _basis = v;
                if (_source != before) _sodiumUnit = null;
              },
              // Only the offered bases; a basis not offered is hidden.
              options: [for (final b in _offered) (b, b, _basisLabel(l10n, b))],
            ),
          ),
          if (_draft?.derivedFromServing ?? false)
            if (serving != null)
              Padding(
                key: const ValueKey('derived_per_serving'),
                padding: const EdgeInsets.only(bottom: SnTokens.space2),
                child: Text(
                  // The serving as currently typed, not the draft's.
                  l10n.confirmDerivedPerServing(formatForDisplay(serving)),
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
          _highlight(
            'serving_size_g',
            Column(
              key: const ValueKey('field:serving_size_g'),
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: _serving.controller,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: InputDecoration(
                    labelText: l10n.confirmServingSize,
                    border: const OutlineInputBorder(),
                    errorText:
                        widget.fieldErrors['serving_size_g'] ??
                        (_serving.valid ? null : l10n.errorValidationError),
                  ),
                ),
                if (servingBox) ...[
                  if (_servingTickRequired)
                    Padding(
                      padding: const EdgeInsets.only(top: SnTokens.space1),
                      child: Text(
                        l10n.confirmWithheldHint,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: SnTokens.verdictCaution,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  _confirmBox(
                    'confirm:serving_size_g',
                    _servingConfirmed,
                    (v) => _servingTicked = v,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: SnTokens.space2),
          if (_sharedShown && _basis != null)
            Padding(
              key: const ValueKey('shared_basis'),
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: Wrap(
                spacing: SnTokens.space2,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Text(l10n.confirmBasis, style: theme.textTheme.bodyMedium),
                  Chip(label: Text(_basisLabel(l10n, _basis!))),
                ],
              ),
            ),
          Text(l10n.confirmLeaveBlankHint, style: theme.textTheme.bodySmall),
          const SizedBox(height: SnTokens.space2),
          for (final f in formNutrientFields) ...[
            _numberField(
              f,
              _shown[f]!,
              suffix: f == 'sodium_mg' && _unitPickerShown
                  ? _sodiumSuffix(l10n)
                  : null,
            ),
            if (f == 'sodium_mg' && _unitPickerShown)
              _chips<ProductCreateSodiumUnit>(
                title: l10n.confirmSodiumUnit,
                keyPrefix: 'sodium_unit',
                requiredChoice: true,
                selected: _sodiumUnit,
                onSelected: (v) => _sodiumUnit = v,
                options: [
                  (
                    ProductCreateSodiumUnit.mg,
                    'mg',
                    l10n.confirmSodiumUnitOptionMg,
                  ),
                  (
                    ProductCreateSodiumUnit.g,
                    'g',
                    l10n.confirmSodiumUnitOptionG,
                  ),
                ],
              ),
          ],
          const SizedBox(height: SnTokens.space2),
          _textList(
            field: 'ingredients',
            title: l10n.confirmIngredients,
            addLabel: l10n.confirmAddIngredient,
            removeLabel: l10n.confirmRemoveIngredient,
            items: _ingredients,
            itemKey: 'ingredient',
          ),
          _statement(l10n, 'allergen_statement', l10n.confirmAllergenStatement),
          _statement(
            l10n,
            'may_contain_statement',
            l10n.confirmMayContainStatement,
          ),
          _highlight(
            'claims',
            TextField(
              key: const ValueKey('field:claims'),
              controller: _claims,
              minLines: 2,
              maxLines: null,
              decoration: InputDecoration(
                labelText: l10n.confirmClaims,
                border: const OutlineInputBorder(),
                errorText: widget.fieldErrors['claims'],
              ),
            ),
          ),
          _chips<ProductCreateVegMark>(
            title: l10n.confirmVegMarkTitle,
            keyPrefix: 'veg_mark',
            selected: _vegMark,
            onSelected: (v) => _vegMark = v,
            options: [
              (ProductCreateVegMark.veg, 'veg', l10n.confirmVegMarkVeg),
              (
                ProductCreateVegMark.nonVeg,
                'non_veg',
                l10n.confirmVegMarkNonVeg,
              ),
              (null, 'none', l10n.confirmVegMarkNone),
            ],
          ),
          const SizedBox(height: SnTokens.space3),
          FilledButton(
            key: const Key('save'),
            onPressed: _canSave && !widget.saving
                ? () => widget.onSave(_body())
                : null,
            child: widget.saving
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(l10n.confirmSave),
          ),
          ...widget.footer,
        ],
      ),
    );
  }

  static String _basisLabel(AppLocalizations l10n, String basis) =>
      basis == 'per_serving'
      ? l10n.confirmBasisOptionPerServing
      : l10n.confirmBasisOptionPer100g;

  static String _categoryLabel(
    AppLocalizations l10n,
    ProductCreateCategory c,
  ) => switch (c) {
    ProductCreateCategory.general => l10n.confirmCategoryOptionGeneral,
    ProductCreateCategory.beverage => l10n.confirmCategoryOptionBeverage,
    ProductCreateCategory.water => l10n.confirmCategoryOptionWater,
    ProductCreateCategory.cheese => l10n.confirmCategoryOptionCheese,
    ProductCreateCategory.fat => l10n.confirmCategoryOptionFat,
    ProductCreateCategory.$unknown => c.toString(),
  };
}
