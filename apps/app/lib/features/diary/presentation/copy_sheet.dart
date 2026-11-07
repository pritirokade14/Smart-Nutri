import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:uuid/uuid.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/diary_repository.dart';
import '../domain/diary_dates.dart';
import '../domain/slot_label.dart';
import 'diary_providers.dart';

/// Copies a meal or a whole day. [fromDate] and [toDate] are calendar dates
/// as the API wrote them. With [askTarget] the sheet first asks which day
/// and meal; otherwise it copies at once.
///
/// One `client_id` is made per sheet and kept while it is open, so a retry
/// (or a double tap) never copies twice.
Future<void> showCopySheet(
  BuildContext context, {
  required String fromDate,
  required String toDate,
  String? fromSlotId,
  bool askTarget = false,
}) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => CopySheet(
    fromDate: fromDate,
    toDate: toDate,
    fromSlotId: fromSlotId,
    askTarget: askTarget,
  ),
);

class CopySheet extends ConsumerStatefulWidget {
  const CopySheet({
    super.key,
    required this.fromDate,
    required this.toDate,
    this.fromSlotId,
    this.askTarget = false,
  });

  final String fromDate;
  final String toDate;
  final String? fromSlotId;
  final bool askTarget;

  static const copyKey = Key('copy-go');
  static const retryKey = Key('copy-retry');
  static const pickDayKey = Key('copy-pick-day');
  static Key slotKey(String id) => Key('copy-slot-$id');

  @override
  ConsumerState<CopySheet> createState() => _CopySheetState();
}

class _CopySheetState extends ConsumerState<CopySheet> {
  /// Fresh per user action; reused by every retry from this sheet.
  final String _clientId = const Uuid().v4();
  late String _toDate = widget.toDate;
  String? _toSlot;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (!widget.askTarget) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _run();
      });
    }
  }

  Future<void> _run() async {
    if (_busy) return;
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final out = await ref
          .read(diaryRepositoryProvider)
          .copy(
            CopyIn(
              clientId: _clientId,
              fromDate: parseDateKey(widget.fromDate)!,
              fromSlotId: widget.fromSlotId,
              toDate: parseDateKey(_toDate)!,
              toSlotId: _toSlot,
            ),
          );
      ref.read(mealsRevisionProvider.notifier).bump();
      await ref.read(analyticsProvider).track('diary_entry_added', {
        'method': 'copy',
      });
      // The count only: never an amount of energy, whatever the setting.
      messenger.showSnackBar(
        SnackBar(content: Text(l10n.diaryCopied(out.created.length))),
      );
      if (mounted) nav.pop();
    } on DiaryFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  Future<void> _pickDay() async {
    final today = parseDateKey(widget.toDate)!;
    final picked = await showDatePicker(
      context: context,
      initialDate: parseDateKey(_toDate)!,
      firstDate: DateTime(today.year - 1, today.month, today.day),
      lastDate: DateTime(today.year, today.month, today.day),
    );
    if (picked != null && mounted) setState(() => _toDate = dateKey(picked));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final slots = ref.watch(mealSlotsProvider).value;
    final date = parseDateKey(_toDate)!;
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space4,
        0,
        SnTokens.space4,
        SnTokens.space4,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(l10n.diaryCopyTo, style: theme.textTheme.titleLarge),
          const SizedBox(height: SnTokens.space3),
          if (widget.askTarget) ...[
            OutlinedButton.icon(
              key: CopySheet.pickDayKey,
              icon: const Icon(Icons.calendar_today_rounded),
              label: Text(
                '${l10n.diaryCopyPickDay}: '
                '${(DateFormat.MMMEd(l10n.localeName)..useNativeDigits = false).format(date)}',
              ),
              onPressed: _busy ? null : _pickDay,
            ),
            if (slots != null) ...[
              const SizedBox(height: SnTokens.space3),
              Text(l10n.diaryCopyPickMeal, style: theme.textTheme.titleSmall),
              Wrap(
                spacing: SnTokens.space2,
                children: [
                  for (final s in slots.items.where((s) => !s.archived))
                    ChoiceChip(
                      key: CopySheet.slotKey(s.id),
                      label: Text(
                        slotLabel(
                          l10n,
                          labelKey: s.labelKey,
                          customLabel: s.customLabel,
                        ),
                      ),
                      selected: _toSlot == s.id,
                      onSelected: _busy
                          ? null
                          : (_) => setState(() => _toSlot = s.id),
                    ),
                ],
              ),
            ],
            const SizedBox(height: SnTokens.space3),
          ],
          if (_error != null) ...[
            InlineErrorBanner(message: _error!),
            const SizedBox(height: SnTokens.space2),
          ],
          if (_error != null)
            PrimaryButton(
              buttonKey: CopySheet.retryKey,
              label: l10n.commonRetry,
              icon: Icons.refresh_rounded,
              busy: _busy,
              onPressed: _run,
            )
          else if (widget.askTarget)
            PrimaryButton(
              buttonKey: CopySheet.copyKey,
              label: l10n.diaryCopyMeal,
              icon: Icons.copy_rounded,
              busy: _busy,
              onPressed: _run,
            )
          else
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
