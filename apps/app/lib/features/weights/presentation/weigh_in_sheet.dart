import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../diary/domain/diary_dates.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../scan/domain/number_text.dart';
import '../data/weights_repository.dart';
import 'weights_providers.dart';

/// Opens the weigh-in sheet. [date] is the day to log (default: the diary's
/// today). Returns true when a weigh-in was saved or queued.
Future<bool?> showWeighInSheet(
  BuildContext context, {
  String? date,
  num? weightKg,
}) => showModalBottomSheet<bool>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => WeighInSheet(date: date, weightKg: weightKg),
);

/// A day and a weight. When the API asks (`weight_needs_confirm`) it shows
/// the last weigh-in and a "Save anyway" button; nothing is judged here.
class WeighInSheet extends ConsumerStatefulWidget {
  const WeighInSheet({super.key, this.date, this.weightKg});

  /// Set when editing a weigh-in (the day cannot change then).
  final String? date;

  /// The current value when editing; null under hidden numbers.
  final num? weightKg;

  static const kgKey = Key('weigh-in-kg');
  static const dateKey = Key('weigh-in-date');
  static const saveKey = Key('weigh-in-save');
  static const confirmKey = Key('weigh-in-confirm');
  static const saveAnywayKey = Key('weigh-in-save-anyway');
  static const errorKey = Key('weigh-in-error');

  @override
  ConsumerState<WeighInSheet> createState() => _WeighInSheetState();
}

class _WeighInSheetState extends ConsumerState<WeighInSheet> {
  late final _kg = TextEditingController(
    text: widget.weightKg == null ? '' : formatForDisplay(widget.weightKg!),
  );

  /// The diary's today (the API decides which day that is); the device date
  /// only when the diary has not loaded (offline).
  late final String _today = _todayKey();
  late String _date = widget.date ?? _today;

  String _todayKey() {
    final today = ref.read(diaryDayProvider(null)).value?.today;
    return today == null ? dateKey(DateTime.now()) : dateKey(today);
  }

  bool _busy = false;
  bool _asking = false;
  num? _previous;
  String? _error;

  @override
  void dispose() {
    _kg.dispose();
    super.dispose();
  }

  num? get _value {
    final p = parseNumber(_kg.text);
    final v = p.value;
    return p.ok && v != null && v > 0 ? v : null;
  }

  Future<void> _pickDate() async {
    final today = parseDateKey(_today)!;
    final picked = await showDatePicker(
      context: context,
      initialDate: parseDateKey(_date)!,
      firstDate: today.subtract(const Duration(days: 400)),
      lastDate: today,
    );
    if (picked != null) {
      setState(() {
        _date = dateKey(picked);
        _asking = false;
      });
    }
  }

  Future<void> _save() async {
    final value = _value;
    if (value == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(weightsRepositoryProvider)
          .log(_date, value, confirmUnusual: _asking);
      refreshWeights(ref);
      if (mounted) Navigator.of(context).pop(true);
    } on WeightsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        if (e.needsConfirm) {
          _asking = true;
          _previous = e.previousKg;
        } else {
          _error = localizedErrorCode(AppLocalizations.of(context), e.code);
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final error = _error;
    final previous = _previous;
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
              widget.date == null ? l10n.weightAdd : l10n.weightEdit,
              style: theme.textTheme.titleLarge,
            ),
            const SizedBox(height: SnTokens.space3),
            ListTile(
              key: WeighInSheet.dateKey,
              contentPadding: EdgeInsets.zero,
              title: Text(l10n.weightDate),
              subtitle: Text(
                (DateFormat.yMMMd(
                  l10n.localeName,
                )..useNativeDigits = false).format(parseDateKey(_date)!),
              ),
              trailing: widget.date == null
                  ? const Icon(Icons.calendar_today_outlined)
                  : null,
              onTap: widget.date == null && !_busy ? _pickDate : null,
            ),
            TextField(
              key: WeighInSheet.kgKey,
              controller: _kg,
              enabled: !_busy,
              autofocus: true,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              onChanged: (_) => setState(() => _asking = false),
              decoration: InputDecoration(
                labelText: l10n.weightTitle,
                helperText: l10n.weightTipSameTime,
              ),
            ),
            if (_asking) ...[
              const SizedBox(height: SnTokens.space2),
              Text(
                previous == null
                    ? l10n.weightConfirmUnusualHidden
                    : l10n.weightConfirmUnusual(formatForDisplay(previous)),
                key: WeighInSheet.confirmKey,
              ),
            ],
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(top: SnTokens.space2),
                child: Text(error, key: WeighInSheet.errorKey),
              ),
            const SizedBox(height: SnTokens.space3),
            PrimaryButton(
              buttonKey: _asking
                  ? WeighInSheet.saveAnywayKey
                  : WeighInSheet.saveKey,
              label: _asking ? l10n.weightSaveAnyway : l10n.mealsLogSave,
              icon: Icons.check_rounded,
              busy: _busy,
              onPressed: _value == null ? null : _save,
            ),
          ],
        ),
      ),
    );
  }
}
