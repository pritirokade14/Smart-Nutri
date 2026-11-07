import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/tokens.g.dart';
import '../domain/slot_label.dart';

/// The longest meal name, in Unicode code points (the API counts the same).
const maxSlotLabelRunes = 30;

/// Stops typing at [maxSlotLabelRunes] code points. A grapheme-based limit
/// would let Devanagari names run past what the API accepts.
class RuneLimitFormatter extends TextInputFormatter {
  const RuneLimitFormatter(this.max);

  final int max;

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    if (newValue.text.runes.length <= max) return newValue;
    return oldValue;
  }
}

/// A name field for a meal: the hint that names are kept as typed, a counter
/// in code points, Save and Cancel. [onSave] returns an inline error message,
/// or null on success. The name is user text: it goes to the API as typed and
/// nowhere else.
class SlotNameEditor extends StatefulWidget {
  const SlotNameEditor({
    super.key,
    required this.initial,
    required this.onSave,
    required this.onCancel,
  });

  final String initial;
  final Future<String?> Function(String label) onSave;
  final VoidCallback onCancel;

  static const fieldKey = Key('slot-name-field');
  static const counterKey = Key('slot-name-counter');
  static const saveKey = Key('slot-name-save');
  static const cancelKey = Key('slot-name-cancel');
  static const errorKey = Key('slot-name-error');

  @override
  State<SlotNameEditor> createState() => _SlotNameEditorState();
}

class _SlotNameEditorState extends State<SlotNameEditor> {
  late final _c = TextEditingController(text: widget.initial);
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    final err = await widget.onSave(_c.text.trim());
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = err;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final runes = _c.text.runes.length;
    final canSave = !_busy && _c.text.trim().isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          key: SlotNameEditor.fieldKey,
          controller: _c,
          enabled: !_busy,
          autofocus: true,
          inputFormatters: const [RuneLimitFormatter(maxSlotLabelRunes)],
          onChanged: (_) => setState(() => _error = null),
          decoration: InputDecoration(
            helperText: l10n.diarySlotsNameHint,
            helperMaxLines: 2,
            errorText: _error,
            // Our own counter: code points, not graphemes.
            counter: Text(
              '$runes/$maxSlotLabelRunes',
              key: SlotNameEditor.counterKey,
              style: theme.textTheme.bodySmall,
            ),
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            TextButton(
              key: SlotNameEditor.cancelKey,
              onPressed: _busy ? null : widget.onCancel,
              child: Text(MaterialLocalizations.of(context).cancelButtonLabel),
            ),
            FilledButton(
              key: SlotNameEditor.saveKey,
              onPressed: canSave ? _save : null,
              child: Text(l10n.mealsLogSave),
            ),
          ],
        ),
      ],
    );
  }
}

/// One meal on the Meals screen: drag handle, name (own label as typed, or
/// the translated default), rename, usual time and remove.
class MealSlotRow extends StatefulWidget {
  const MealSlotRow({
    super.key,
    required this.slot,
    required this.index,
    required this.canRemove,
    required this.onRename,
    required this.onResetName,
    required this.onPickTime,
    required this.onClearTime,
    required this.onRemove,
  });

  final MealSlotOut slot;
  final int index;
  final bool canRemove;
  final Future<String?> Function(String label) onRename;
  final VoidCallback onResetName;
  final VoidCallback onPickTime;
  final VoidCallback onClearTime;
  final VoidCallback onRemove;

  static Key rowKey(String id) => Key('meal-slot-$id');
  static Key titleKey(String id) => Key('meal-slot-title-$id');
  static Key renameKey(String id) => Key('meal-slot-rename-$id');
  static Key resetKey(String id) => Key('meal-slot-reset-$id');
  static Key timeKey(String id) => Key('meal-slot-time-$id');
  static Key clearTimeKey(String id) => Key('meal-slot-clear-time-$id');
  static Key removeKey(String id) => Key('meal-slot-remove-$id');
  static Key handleKey(String id) => Key('meal-slot-handle-$id');

  @override
  State<MealSlotRow> createState() => _MealSlotRowState();
}

class _MealSlotRowState extends State<MealSlotRow> {
  bool _editing = false;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final slot = widget.slot;
    final title = slotLabel(
      l10n,
      labelKey: slot.labelKey,
      customLabel: slot.customLabel,
    );
    final window = slot.defaultTimeWindow;
    return Card(
      key: MealSlotRow.rowKey(slot.id),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space2),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                ReorderableDragStartListener(
                  index: widget.index,
                  child: Padding(
                    padding: const EdgeInsets.all(SnTokens.space2),
                    child: Icon(
                      Icons.drag_handle_rounded,
                      key: MealSlotRow.handleKey(slot.id),
                      semanticLabel: l10n.diarySlotsReorder,
                    ),
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        key: MealSlotRow.titleKey(slot.id),
                        style: theme.textTheme.titleMedium,
                      ),
                      if (window != null)
                        Text(
                          '${window.start} - ${window.end}',
                          style: theme.textTheme.bodySmall,
                        ),
                    ],
                  ),
                ),
                IconButton(
                  key: MealSlotRow.renameKey(slot.id),
                  tooltip: l10n.diarySlotsRename,
                  icon: const Icon(Icons.edit_outlined),
                  onPressed: () => setState(() => _editing = true),
                ),
                IconButton(
                  key: MealSlotRow.removeKey(slot.id),
                  tooltip: widget.canRemove
                      ? l10n.diarySlotsRemove
                      : l10n.diarySlotsLastActive,
                  icon: const Icon(Icons.delete_outline_rounded),
                  onPressed: widget.canRemove ? widget.onRemove : null,
                ),
              ],
            ),
            if (!widget.canRemove)
              Padding(
                padding: const EdgeInsets.only(left: SnTokens.space2),
                child: Text(
                  l10n.diarySlotsLastActive,
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (_editing)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: SnTokens.space2,
                ),
                child: SlotNameEditor(
                  initial: slot.customLabel ?? title,
                  onCancel: () => setState(() => _editing = false),
                  onSave: (label) async {
                    final err = await widget.onRename(label);
                    if (err == null && mounted) {
                      setState(() => _editing = false);
                    }
                    return err;
                  },
                ),
              ),
            Wrap(
              children: [
                if (slot.isDefault && slot.customLabel != null)
                  TextButton(
                    key: MealSlotRow.resetKey(slot.id),
                    onPressed: widget.onResetName,
                    child: Text(l10n.diarySlotsResetName),
                  ),
                TextButton.icon(
                  key: MealSlotRow.timeKey(slot.id),
                  icon: const Icon(Icons.schedule_rounded),
                  label: Text(l10n.diarySlotsTimeWindow),
                  onPressed: widget.onPickTime,
                ),
                if (window != null)
                  IconButton(
                    key: MealSlotRow.clearTimeKey(slot.id),
                    tooltip: MaterialLocalizations.of(
                      context,
                    ).deleteButtonTooltip,
                    icon: const Icon(Icons.close_rounded),
                    onPressed: widget.onClearTime,
                  ),
              ],
            ),
            if (_editing || window == null)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: SnTokens.space2,
                ),
                child: Text(
                  l10n.diarySlotsTimeWindowHint,
                  style: theme.textTheme.bodySmall,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
