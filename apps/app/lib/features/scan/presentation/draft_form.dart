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
/// (Ruling R17). Safety rules (task 8/9 addendum, R19):
/// - blanks stay blank and are sent as null, never 0;
/// - withheld values, the serving size, the basis, the category and an
///   unconfirmed sodium unit are never confirmed on the user's behalf;
/// - for a `derived_from_serving` draft the printed per-serving column is
///   shown and sent (basis per_serving), never the derived per-100 g values.
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
  State<DraftForm> createState() => _DraftFormState();
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

  bool get edited => controller.text != initialText;
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

bool _hasEngineValues(DraftNutrients? n) =>
    n != null && engineFields.any((f) => _nutrient(n, f) != null);

const _statementFields = ['allergen_statement', 'may_contain_statement'];

class _DraftFormState extends State<DraftForm> {
  late final ProductDraft? _draft = widget.draft;
  late final List<DraftWarning> _warnings = [
    for (final w in _draft?.warnings ?? const <String>[]) DraftWarning.parse(w),
  ];
  late final Set<String> _codes = {for (final w in _warnings) w.code};
  late final List<String> _rawWarnings = _draft?.warnings ?? const [];

  bool get _scan => _draft != null;
  bool get _mismatch => _codes.contains('basis_mismatch');
  bool get _derived => _draft?.derivedFromServing ?? false;

  /// One column for both bases (manual entry; a basis mismatch, where the
  /// basis only says what the printed numbers mean).
  late final bool _sharedColumn;
  late final Map<String, _NumInput> _per100;
  late final Map<String, _NumInput> _perServing;

  /// The printed column a shared column was taken from (for warning paths).
  late final String _sharedSource;

  ProductCreateBasis? _basis;
  ProductCreateCategory? _category;
  ProductCreateSodiumUnit? _sodiumUnit;
  ProductCreateVegMark? _vegMark;

  /// Withheld fields the user ticked or edited.
  final Set<String> _confirmed = {};
  bool _servingConfirmed = false;
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
      _sharedColumn = true;
      _sharedSource = 'per_100g';
      _per100 = column(null);
      _perServing = _per100;
      _basis = ProductCreateBasis.per100g;
    } else if (draft.derivedFromServing) {
      // R19: the per-100 g values were derived by the server; nothing was
      // printed per 100 g. Show and send the printed per-serving column.
      _sharedColumn = false;
      _sharedSource = 'per_serving';
      _per100 = column(null);
      _perServing = column(draft.perServing);
      _basis = ProductCreateBasis.perServing;
    } else if (_mismatch) {
      final fromServing =
          !_hasEngineValues(draft.per100g) &&
          _hasEngineValues(draft.perServing);
      _sharedColumn = true;
      _sharedSource = fromServing ? 'per_serving' : 'per_100g';
      _per100 = column(fromServing ? draft.perServing : draft.per100g);
      _perServing = _per100;
      _basis = null; // forced choice
    } else {
      _sharedColumn = false;
      _sharedSource = 'per_100g';
      _per100 = column(draft.per100g);
      _perServing = column(draft.perServing);
      _basis = ProductCreateBasis.per100g;
    }
    if (draft != null &&
        !_codes.contains('category_unknown') &&
        !_codes.contains('category_check')) {
      final c = ProductCreateCategory.fromJson(draft.category.json ?? '');
      _category = c == ProductCreateCategory.$unknown ? null : c;
    }
    final veg = ProductCreateVegMark.fromJson(draft?.vegMark?.json ?? '');
    _vegMark = veg == ProductCreateVegMark.$unknown ? null : veg;

    for (final column in {_per100, _perServing}) {
      for (final e in column.entries) {
        e.value.controller.addListener(
          () => _onNutrientChanged(e.key, e.value),
        );
      }
    }
    _serving.controller.addListener(() {
      if (_serving.edited) _servingConfirmed = true;
      setState(() {});
    });
    for (final c in [_name, ..._statements.values]) {
      c.addListener(() => setState(() {}));
    }
  }

  void _onNutrientChanged(String field, _NumInput input) {
    // Editing a withheld value is confirming it.
    if (input.edited && _withheld.contains(field)) _confirmed.add(field);
    setState(() {});
  }

  @override
  void dispose() {
    for (final column in {_per100, _perServing}) {
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

  // --- derived state ------------------------------------------------------

  Map<String, _NumInput> get _shown => _sharedColumn
      ? _per100
      : (_basis == ProductCreateBasis.perServing ? _perServing : _per100);

  /// The printed column the shown numbers came from.
  String get _shownColumn => _sharedColumn
      ? _sharedSource
      : (_basis == ProductCreateBasis.perServing ? 'per_serving' : 'per_100g');

  Set<String> get _columns => {_shownColumn, ?_basis?.json};

  /// R19: any unit-less sodium on either column, with sodium not blank.
  bool get _unitPickerShown =>
      _scan &&
      _rawWarnings.any(
        (w) => w.startsWith('unit_unconfirmed:') && w.endsWith('.sodium_mg'),
      ) &&
      !_shown['sodium_mg']!.isBlank;

  /// Engine fields the server stores only when confirmed (mirrors the save
  /// rules): the draft's list (answered by the basis on a mismatch), plus an
  /// upper-bound protein or fibre on the column in use. A unit-less sodium is
  /// confirmed by choosing its unit instead (R19).
  Set<String> get _withheld {
    if (!_scan) return const {};
    final out = <String>{
      if (!_mismatch)
        for (final f in _draft!.engineWithheld)
          if (f.json case final String name) name,
    };
    for (final f in const ['protein_g', 'fiber_g']) {
      if (_columns.any((c) => _rawWarnings.contains('upper_bound:$c.$f'))) {
        out.add(f);
      }
    }
    if (_unitPickerShown) out.remove('sodium_mg');
    return out;
  }

  bool get _servingShown =>
      !_scan ||
      _draft!.servingSizeG != null ||
      _derived ||
      _basis == ProductCreateBasis.perServing;

  /// R18/R19: per-serving values are stored only with a confirmed serving.
  bool get _servingTickRequired =>
      _scan && (_derived || _basis == ProductCreateBasis.perServing);

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
      !(_servingTickRequired && !_servingConfirmed) &&
      !(_basis == ProductCreateBasis.perServing && _serving.value == null) &&
      _invalidFields.isEmpty &&
      _statementFields.every(
        (f) => !_blankNeedsConfirm(f) || _blankConfirmed.contains(f),
      );

  // --- body ---------------------------------------------------------------

  ProductCreate _body() {
    final col = _shown;
    num? v(String f) => col[f]!.value;
    String? text(TextEditingController c) =>
        c.text.trim().isEmpty ? null : c.text;
    final withheld = _withheld;
    final confirmed = <ProductCreateConfirmedFields>[
      if (_scan) ...[
        for (final f in engineFields)
          if (withheld.contains(f) && _confirmed.contains(f))
            ProductCreateConfirmedFields.fromJson(f),
        if (_servingShown && _servingConfirmed)
          ProductCreateConfirmedFields.servingSizeG,
      ],
    ];
    return ProductCreate(
      scanId: _scan ? widget.scanId : null,
      barcode: widget.barcode,
      name: _name.text.trim(),
      brand: text(_brand)?.trim(),
      category: _category!,
      basis: _basis!,
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
      servingSizeG: _servingShown ? _serving.value : null,
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
    final withheld = _withheld.contains(field);
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
          if (withheld) ...[
            Padding(
              padding: const EdgeInsets.only(top: SnTokens.space1),
              child: Text(
                l10n.confirmWithheldHint,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            _confirmBox(
              'confirm:$field',
              _confirmed.contains(field),
              (v) => v ? _confirmed.add(field) : _confirmed.remove(field),
            ),
          ],
        ],
      ),
    );
  }

  Widget _sodiumSuffix(AppLocalizations l10n) {
    final unit = !_unitPickerShown
        ? l10n.confirmSodiumUnitOptionMg
        : switch (_sodiumUnit) {
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
    return _highlight(
      field,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
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
    final draftServing = _draft?.servingSizeG;
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
            _chips<ProductCreateBasis>(
              title: l10n.confirmBasis,
              keyPrefix: 'basis',
              requiredChoice: true,
              selected: _basis,
              onSelected: (v) => _basis = v,
              options: [
                (
                  ProductCreateBasis.per100g,
                  'per_100g',
                  l10n.confirmBasisOptionPer100g,
                ),
                (
                  ProductCreateBasis.perServing,
                  'per_serving',
                  l10n.confirmBasisOptionPerServing,
                ),
              ],
            ),
          ),
          if (_derived && draftServing != null)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: Text(
                l10n.confirmDerivedPerServing(formatForDisplay(draftServing)),
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          if (_servingShown)
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
                  if (_scan) ...[
                    if (_servingTickRequired && !_servingConfirmed)
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
                      (v) => _servingConfirmed = v,
                    ),
                  ],
                ],
              ),
            ),
          const SizedBox(height: SnTokens.space2),
          Text(l10n.confirmLeaveBlankHint, style: theme.textTheme.bodySmall),
          const SizedBox(height: SnTokens.space2),
          for (final f in formNutrientFields) ...[
            _numberField(
              f,
              _shown[f]!,
              suffix: f == 'sodium_mg' ? _sodiumSuffix(l10n) : null,
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
