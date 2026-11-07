import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/data/meals_repository.dart';
import '../../meals/domain/meal_draft.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../scan/domain/number_text.dart';
import '../domain/diary_dates.dart';
import '../domain/slot_label.dart';
import 'diary_providers.dart';
import 'quick_add_form.dart';

/// Where the sheet sends the user next: the existing flows.
enum AddFoodNext { search, barcode, label }

enum _Segment { recent, search, barcode, label, quick }

/// Logs [draft] (online or queued) and sends `diary_entry_added` with the
/// method only. Throws [MealsFailure] when the API refuses it.
Future<MealLogResult> logDiaryEntry(
  WidgetRef ref,
  MealDraft draft,
  String method,
) async {
  final result = await ref.read(mealsRepositoryProvider).log(draft);
  ref.read(mealsRevisionProvider.notifier).bump();
  // The method only: no name, slot label, nutrient or portion.
  await ref.read(analyticsProvider).track('diary_entry_added', {
    'method': method,
  });
  return result;
}

/// Opens the add-food sheet for [day]. [slotId] preselects a slot (its Add
/// button); without it the API's suggestion is preselected. Returns the
/// flow the user chose, or null.
Future<AddFoodNext?> showAddFoodSheet(
  BuildContext context, {
  required DiaryDayOut day,
  String? slotId,
}) => showModalBottomSheet<AddFoodNext>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => AddFoodSheet(day: day, slotId: slotId),
);

class AddFoodSheet extends ConsumerStatefulWidget {
  const AddFoodSheet({super.key, required this.day, this.slotId});

  final DiaryDayOut day;
  final String? slotId;

  static Key segmentKey(String name) => Key('add-food-segment-$name');
  static Key chipKey(String slotId) => Key('add-food-slot-$slotId');
  static Key recentKey(String productId) => Key('add-food-recent-$productId');

  @override
  ConsumerState<AddFoodSheet> createState() => _AddFoodSheetState();
}

class _AddFoodSheetState extends ConsumerState<AddFoodSheet> {
  _Segment _segment = _Segment.recent;
  String? _picked;
  bool _busy = false;
  String? _error;

  /// A past day sends `local_date`; today sends the time (the API decides
  /// which day is today).
  String? get _localDate =>
      dateKey(widget.day.date) == dateKey(widget.day.today)
      ? null
      : dateKey(widget.day.date);

  /// The slot to send: the chip, else the tapped slot, else none (the API
  /// picks one).
  String? _slot(MealSlotsOut? slots) =>
      _picked ?? widget.slotId ?? slots?.suggestedSlotId;

  Future<void> _log(MealDraft draft, String method) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await logDiaryEntry(ref, draft, method);
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            result is MealLogged
                ? l10n.mealsLogSavedYou
                : l10n.mealsQueuedOffline,
          ),
        ),
      );
      if (mounted) nav.pop();
    } on MealsFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final slots = ref.watch(mealSlotsProvider).value;
    final slotId = _slot(slots);
    final labels = <_Segment, String>{
      _Segment.recent: l10n.foodsRecent,
      _Segment.search: l10n.searchTitle,
      _Segment.barcode: l10n.navScan,
      _Segment.label: l10n.labelTitle,
      _Segment.quick: l10n.foodsQuickAdd,
    };
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
            Text(l10n.diaryAdd, style: theme.textTheme.titleLarge),
            const SizedBox(height: SnTokens.space3),
            // Hidden when the slot list has not loaded: the API picks.
            if (slots != null) ...[
              Wrap(
                spacing: SnTokens.space2,
                runSpacing: SnTokens.space2,
                children: [
                  for (final s in slots.items.where((s) => !s.archived))
                    ChoiceChip(
                      key: AddFoodSheet.chipKey(s.id),
                      label: Text(
                        slotLabel(
                          l10n,
                          labelKey: s.labelKey,
                          customLabel: s.customLabel,
                        ),
                      ),
                      selected: s.id == slotId,
                      onSelected: _busy
                          ? null
                          : (_) => setState(() => _picked = s.id),
                    ),
                ],
              ),
              const SizedBox(height: SnTokens.space3),
            ],
            Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space2,
              children: [
                for (final seg in _Segment.values)
                  ChoiceChip(
                    key: AddFoodSheet.segmentKey(seg.name),
                    label: Text(labels[seg]!),
                    selected: seg == _segment,
                    onSelected: (_) => _onSegment(seg, slotId),
                  ),
              ],
            ),
            const SizedBox(height: SnTokens.space3),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: SnTokens.space2),
                child: InlineErrorBanner(message: _error!),
              ),
            if (_segment == _Segment.recent) _recents(slotId),
            if (_segment == _Segment.quick)
              QuickAddForm(
                busy: _busy,
                onSubmit: (v) => _log(
                  MealDraft(
                    memberId: widget.day.memberId,
                    eatenAt: DateTime.now().toUtc(),
                    mealSlotId: slotId,
                    localDate: _localDate,
                    quickName: v.name,
                    quickEnergyKcal: v.energyKcal,
                    quickProteinG: v.proteinG,
                    quickFatG: v.fatG,
                    quickCarbsG: v.carbsG,
                    quickFibreG: v.fibreG,
                    displayName: v.name,
                  ),
                  'quick_add',
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _onSegment(_Segment seg, String? slotId) {
    switch (seg) {
      case _Segment.search:
        _leave(AddFoodNext.search, 'search', slotId);
      case _Segment.barcode:
        _leave(AddFoodNext.barcode, 'barcode', slotId);
      case _Segment.label:
        _leave(AddFoodNext.label, 'label', slotId);
      case _Segment.recent:
      case _Segment.quick:
        setState(() => _segment = seg);
    }
  }

  /// The existing search, scanner and label flows take over; their portion
  /// step logs into this slot and day.
  void _leave(AddFoodNext next, String method, String? slotId) {
    ref
        .read(diaryAddContextProvider.notifier)
        .set(
          DiaryAddContext(
            method: method,
            slotId: slotId,
            localDate: _localDate,
          ),
        );
    Navigator.of(context).pop(next);
  }

  Widget _recents(String? slotId) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(diaryRecentsProvider(slotId))
        .when(
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(l10n, apiErrorCode(e)),
            onRetry: () => ref.invalidate(diaryRecentsProvider(slotId)),
          ),
          data: (items) => Column(
            children: [
              for (final r in items)
                ListTile(
                  key: AddFoodSheet.recentKey(
                    r.productId ?? r.barcode ?? r.name,
                  ),
                  contentPadding: EdgeInsets.zero,
                  enabled: !_busy,
                  title: Text(r.name),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(l10n.diaryGramsLine(formatForDisplay(r.grams))),
                      if (r.attribution != null && r.barcode != null)
                        OffAttribution(barcode: r.barcode!),
                    ],
                  ),
                  onTap: () => _log(
                    MealDraft(
                      memberId: widget.day.memberId,
                      productId: r.productId,
                      barcode: r.productId == null ? r.barcode : null,
                      grams: r.grams,
                      eatenAt: DateTime.now().toUtc(),
                      mealSlotId: slotId,
                      localDate: _localDate,
                      displayName: r.name,
                    ),
                    'recent',
                  ),
                ),
            ],
          ),
        );
  }
}
