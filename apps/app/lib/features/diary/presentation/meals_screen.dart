import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/states.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/diary_repository.dart';
import 'diary_providers.dart';
import 'meal_slot_row.dart';

/// The most meals a person can have.
const maxActiveSlots = 6;

/// "Edit meals": list, add, rename, reorder and remove. Online only. It
/// shows what the API sent; names are user text, never translated and never
/// in analytics (this screen sends no events at all).
class MealsScreen extends ConsumerStatefulWidget {
  const MealsScreen({super.key});

  static const listKey = Key('meals-list');
  static const addKey = Key('meals-add');
  static const limitKey = Key('meals-limit');
  static const errorKey = Key('meals-error');
  static const retryKey = Key('meals-retry');
  static const removeNoteKey = Key('meals-remove-note');
  static const removeConfirmKey = Key('meals-remove-confirm');

  @override
  ConsumerState<MealsScreen> createState() => _MealsScreenState();
}

class _MealsScreenState extends ConsumerState<MealsScreen> {
  /// The order shown while a reorder call is in flight.
  List<MealSlotOut>? _local;
  bool _adding = false;
  String? _error;

  String _message(Object e) => localizedErrorCode(
    AppLocalizations.of(context),
    e is DiaryFailure ? e.code : null,
  );

  void _changed() {
    ref.read(mealsRevisionProvider.notifier).bump();
  }

  /// Runs a write; an error shows as a banner, `null` return means ok.
  Future<bool> _run(Future<void> Function() call) async {
    setState(() => _error = null);
    try {
      await call();
      _changed();
      return true;
    } on DiaryFailure catch (e) {
      if (mounted) setState(() => _error = _message(e));
      return false;
    }
  }

  /// For the name editors: the inline error text, or null when it worked.
  Future<String?> _inline(Future<void> Function() call) async {
    try {
      await call();
      _changed();
      return null;
    } on DiaryFailure catch (e) {
      return _message(e);
    }
  }

  Future<void> _reorder(List<MealSlotOut> items, int from, int to) async {
    final next = [...items];
    next.insert(to, next.removeAt(from));
    setState(() => _local = next);
    final ok = await _run(
      () => ref.read(mealSlotsRepositoryProvider).reorder([
        for (final s in next) s.id,
      ]),
    );
    if (mounted) setState(() => _local = null);
    if (!ok) _changed();
  }

  Future<void> _pickTime(MealSlotOut slot) async {
    final start = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 8, minute: 0),
    );
    if (start == null || !mounted) return;
    final end = await showTimePicker(context: context, initialTime: start);
    if (end == null || !mounted) return;
    String hhmm(TimeOfDay t) =>
        '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    await _run(
      () => ref
          .read(mealSlotsRepositoryProvider)
          .rename(
            slot.id,
            window: TimeWindow(start: hhmm(start), end: hhmm(end)),
          ),
    );
  }

  Future<void> _remove(MealSlotOut slot) async {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.diarySlotsRemove),
        content: Text(
          l10n.diarySlotsRemoveNote,
          key: MealsScreen.removeNoteKey,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(material.cancelButtonLabel),
          ),
          TextButton(
            key: MealsScreen.removeConfirmKey,
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.diarySlotsRemove),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    await _run(() => ref.read(mealSlotsRepositoryProvider).archive(slot.id));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final slots = ref.watch(mealSlotsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.diarySlotsManage)),
      body: slots.when(
        skipLoadingOnRefresh: true,
        loading: () => const SingleChildScrollView(
          padding: EdgeInsets.all(SnTokens.space4),
          child: LoadingSkeleton(card: true, lines: 4),
        ),
        error: (e, _) => Center(
          child: SingleChildScrollView(
            child: ErrorState(
              message: _message(e),
              onRetry: () => ref.invalidate(mealSlotsProvider),
            ),
          ),
        ),
        data: (out) {
          final items = _local ?? out.items.where((s) => !s.archived).toList();
          final atLimit = items.length >= maxActiveSlots;
          return ListView(
            padding: const EdgeInsets.all(SnTokens.space4),
            children: [
              if (_error case final msg?)
                Padding(
                  padding: const EdgeInsets.only(bottom: SnTokens.space3),
                  child: InlineErrorBanner(
                    key: MealsScreen.errorKey,
                    message: msg,
                  ),
                ),
              ReorderableListView(
                key: MealsScreen.listKey,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                buildDefaultDragHandles: false,
                onReorderItem: (from, to) => _reorder(items, from, to),
                children: [
                  for (final (i, s) in items.indexed)
                    MealSlotRow(
                      key: ValueKey(s.id),
                      slot: s,
                      index: i,
                      canRemove: items.length > 1,
                      onRename: (label) => _inline(
                        () => ref
                            .read(mealSlotsRepositoryProvider)
                            .rename(s.id, label: label),
                      ),
                      onResetName: () => _run(
                        () => ref
                            .read(mealSlotsRepositoryProvider)
                            .rename(s.id, clearName: true),
                      ),
                      onPickTime: () => _pickTime(s),
                      onClearTime: () => _run(
                        () => ref
                            .read(mealSlotsRepositoryProvider)
                            .rename(s.id, clearWindow: true),
                      ),
                      onRemove: () => _remove(s),
                    ),
                ],
              ),
              const SizedBox(height: SnTokens.space3),
              if (_adding)
                SlotNameEditor(
                  initial: '',
                  onCancel: () => setState(() => _adding = false),
                  onSave: (label) async {
                    final err = await _inline(
                      () => ref.read(mealSlotsRepositoryProvider).create(label),
                    );
                    if (err == null && mounted) setState(() => _adding = false);
                    return err;
                  },
                )
              else
                OutlinedButton.icon(
                  key: MealsScreen.addKey,
                  icon: const Icon(Icons.add_rounded),
                  label: Text(l10n.diarySlotsAdd),
                  onPressed: atLimit
                      ? null
                      : () => setState(() => _adding = true),
                ),
              if (atLimit)
                Padding(
                  padding: const EdgeInsets.only(top: SnTokens.space2),
                  child: Text(
                    l10n.diarySlotsLimit('$maxActiveSlots'),
                    key: MealsScreen.limitKey,
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
