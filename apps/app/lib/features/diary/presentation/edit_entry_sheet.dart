import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../scan/domain/number_text.dart';
import '../data/diary_repository.dart';
import 'diary_providers.dart';
import 'move_entry_sheet.dart';

/// Opens the edit sheet for [entry]. Editing and removing need a connection
/// (Ruling E19). Returns true when something changed.
Future<bool?> showEditEntrySheet(BuildContext context, MealOut entry) =>
    showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => EditEntrySheet(entry: entry),
    );

/// A grams stepper for a product entry, or the quick fields for a quick
/// add. Save sends only what changed (`mealsUpdate`); Remove asks first.
class EditEntrySheet extends ConsumerStatefulWidget {
  const EditEntrySheet({super.key, required this.entry});

  final MealOut entry;

  static const gramsKey = Key('edit-entry-grams');
  static const minusKey = Key('edit-entry-minus');
  static const plusKey = Key('edit-entry-plus');
  static const saveKey = Key('edit-entry-save');
  static const removeKey = Key('edit-entry-remove');
  static const moveKey = Key('edit-entry-move');
  static const nameKey = Key('edit-quick-name');
  static const energyKey = Key('edit-quick-energy');
  static const proteinKey = Key('edit-quick-protein');
  static const fatKey = Key('edit-quick-fat');
  static const carbsKey = Key('edit-quick-carbs');
  static const fibreKey = Key('edit-quick-fibre');

  /// The stepper moves by this many grams.
  static const step = 10;
  static const maxGrams = 5000;

  @override
  ConsumerState<EditEntrySheet> createState() => _EditEntrySheetState();
}

class _EditEntrySheetState extends ConsumerState<EditEntrySheet> {
  late final _grams = TextEditingController(
    text: widget.entry.grams == null
        ? ''
        : formatForDisplay(widget.entry.grams!),
  );
  late final _name = TextEditingController(text: widget.entry.productName);
  late final _energy = TextEditingController(
    text: _text(widget.entry.nutrients.energyKcal),
  );
  late final _protein = TextEditingController(
    text: _text(widget.entry.nutrients.proteinG),
  );
  late final _fat = TextEditingController(
    text: _text(widget.entry.nutrients.fatG),
  );
  late final _carbs = TextEditingController(
    text: _text(widget.entry.nutrients.carbsG),
  );
  late final _fibre = TextEditingController(
    text: _text(widget.entry.nutrients.fibreG),
  );
  bool _busy = false;
  String? _error;

  static String _text(num? v) => v == null ? '' : formatForDisplay(v);

  bool get _quick => widget.entry.sourceKind == MealOutSourceKind.quickAdd;

  /// A quick add whose energy is hidden or unknown cannot be edited here: the
  /// API replaces every quick value, so blank fields would wipe values the
  /// user cannot see. It can only be removed.
  bool get _quickEditable =>
      _quick && widget.entry.nutrients.energyKcal != null;

  @override
  void dispose() {
    for (final c in [_grams, _name, _energy, _protein, _fat, _carbs, _fibre]) {
      c.dispose();
    }
    super.dispose();
  }

  num? get _gramsValue {
    final p = parseNumber(_grams.text);
    final v = p.value;
    if (!p.ok || v == null || v <= 0 || v > EditEntrySheet.maxGrams) {
      return null;
    }
    return v;
  }

  void _bump(int delta) {
    final v = (_gramsValue ?? 0) + delta;
    if (v <= 0 || v > EditEntrySheet.maxGrams) return;
    setState(() => _grams.text = formatForDisplay(v));
  }

  /// Blank is null, never 0.
  num? _optional(TextEditingController c) => parseNumber(c.text).value;

  bool get _canSave {
    if (_busy) return false;
    if (_quick) {
      final e = parseNumber(_energy.text).value;
      return _quickEditable && e != null && e > 0;
    }
    final g = _gramsValue;
    return g != null && g != widget.entry.grams;
  }

  Future<void> _run(Future<void> Function() call) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await call();
      ref.read(mealsRevisionProvider.notifier).bump();
      if (mounted) Navigator.of(context).pop(true);
    } on DiaryFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  Future<void> _save() => _run(() async {
    final repo = ref.read(diaryRepositoryProvider);
    final patch = _quick
        ? MealPatch(
            quick: QuickIn(
              name: _name.text.trim().isEmpty ? null : _name.text.trim(),
              energyKcal: parseNumber(_energy.text).value,
              proteinG: _optional(_protein),
              fatG: _optional(_fat),
              carbsG: _optional(_carbs),
              fibreG: _optional(_fibre),
            ),
          )
        : MealPatch(grams: _gramsValue);
    await repo.update(widget.entry.id, patch);
  });

  Future<void> _remove() async {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(l10n.diaryDeleteConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(material.cancelButtonLabel),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.diaryDelete),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    await _run(() => ref.read(diaryRepositoryProvider).delete(widget.entry.id));
  }

  Future<void> _move() async {
    final moved = await showMoveEntrySheet(context, widget.entry);
    if (moved == true && mounted) Navigator.of(context).pop(true);
  }

  Widget _numberField(
    Key key,
    TextEditingController c,
    String label, {
    String? helper,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: SnTokens.space2),
    child: TextField(
      key: key,
      controller: c,
      enabled: !_busy,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      onChanged: (_) => setState(() {}),
      decoration: InputDecoration(labelText: label, helperText: helper),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final error = _error;
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
            Text(
              _quick && widget.entry.productName.trim().isEmpty
                  ? l10n.diaryQuickAddName
                  : widget.entry.productName,
              style: theme.textTheme.titleLarge,
            ),
            const SizedBox(height: SnTokens.space3),
            if (_quick) ...[
              if (_quickEditable) ...[
                TextField(
                  key: EditEntrySheet.nameKey,
                  controller: _name,
                  enabled: !_busy,
                  maxLength: 60,
                  decoration: InputDecoration(
                    labelText: l10n.diaryQuickAddNameLabel,
                  ),
                ),
                _numberField(
                  EditEntrySheet.energyKey,
                  _energy,
                  l10n.diaryQuickAddEnergy,
                ),
                _numberField(
                  EditEntrySheet.proteinKey,
                  _protein,
                  l10n.diaryQuickAddProtein,
                ),
                _numberField(
                  EditEntrySheet.fatKey,
                  _fat,
                  l10n.diaryQuickAddFat,
                ),
                _numberField(
                  EditEntrySheet.carbsKey,
                  _carbs,
                  l10n.diaryQuickAddCarbs,
                ),
                _numberField(
                  EditEntrySheet.fibreKey,
                  _fibre,
                  l10n.diaryQuickAddFibre,
                  helper: l10n.foodsBlankIsUnknown,
                ),
              ],
            ] else
              Row(
                children: [
                  IconButton(
                    key: EditEntrySheet.minusKey,
                    icon: const Icon(Icons.remove_circle_outline_rounded),
                    onPressed: _busy ? null : () => _bump(-EditEntrySheet.step),
                  ),
                  Expanded(
                    child: TextField(
                      key: EditEntrySheet.gramsKey,
                      controller: _grams,
                      enabled: !_busy,
                      textAlign: TextAlign.center,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      onChanged: (_) => setState(() {}),
                      decoration: InputDecoration(
                        labelText: l10n.mealsLogAmountGrams,
                      ),
                    ),
                  ),
                  IconButton(
                    key: EditEntrySheet.plusKey,
                    icon: const Icon(Icons.add_circle_outline_rounded),
                    onPressed: _busy ? null : () => _bump(EditEntrySheet.step),
                  ),
                ],
              ),
            if (error != null) ...[
              const SizedBox(height: SnTokens.space3),
              InlineErrorBanner(message: error),
            ],
            const SizedBox(height: SnTokens.space4),
            if (!_quick || _quickEditable)
              PrimaryButton(
                buttonKey: EditEntrySheet.saveKey,
                label: l10n.mealsLogSave,
                icon: Icons.check_rounded,
                busy: _busy,
                onPressed: _canSave ? _save : null,
              ),
            TextButton.icon(
              key: EditEntrySheet.moveKey,
              icon: const Icon(Icons.drive_file_move_outlined),
              label: Text(l10n.diaryMove),
              onPressed: _busy ? null : _move,
            ),
            TextButton.icon(
              key: EditEntrySheet.removeKey,
              icon: const Icon(Icons.delete_outline_rounded),
              label: Text(l10n.diaryDelete),
              onPressed: _busy ? null : _remove,
            ),
          ],
        ),
      ),
    );
  }
}
