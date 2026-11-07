import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/states.dart';
import '../../history/presentation/summary_display.dart';
import '../../meals/domain/meal_summary.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart'
    show consentStateProvider;
import '../../targets/data/targets_repository.dart';
import '../../targets/presentation/eye_toggle.dart';
import '../../targets/presentation/guide_result_step.dart' show statusMessage;
import '../../targets/presentation/targets_explanation.dart';
import '../../targets/presentation/targets_providers.dart';
import '../data/diary_repository.dart';
import '../../../core/storage/meal_queue.dart';
import '../domain/diary_dates.dart';
import 'add_food_sheet.dart';
import 'copy_sheet.dart';
import 'day_header.dart';
import 'day_menu.dart';
import 'move_entry_sheet.dart';
import 'pending_entries.dart';
import 'pick_slot_again.dart';
import 'week_view.dart';
import 'diary_providers.dart';
import 'diary_rings.dart';
import 'edit_entry_sheet.dart';
import 'slot_section.dart';
import 'sync_banner.dart';

/// The Diary tab: one day of the account holder. Renders only what
/// `diary_day_get` returns; it never adds up a total or works out a
/// remainder, a date or a target.
class DiaryScreen extends ConsumerStatefulWidget {
  const DiaryScreen({super.key, this.date});

  /// The calendar date to show (`2026-11-07`), or null for the account's
  /// today (the API decides which day that is).
  final String? date;

  static const emptyKey = Key('diary-empty');
  static const noGuideKey = Key('diary-no-guide');
  static const setupKey = Key('diary-setup');
  static const consentKey = Key('diary-consent');
  static const consentButtonKey = Key('diary-consent-grant');
  static const bandsKey = Key('diary-bands');
  static Key bandKey(String n) => Key('diary-band-$n');
  static const partialKey = Key('diary-partial-badge');
  static const hiddenNoteKey = Key('diary-hidden-note');
  static const pendingReviewKey = Key('diary-pending-review');
  static const addFabKey = Key('diary-add-fab');

  @override
  ConsumerState<DiaryScreen> createState() => _DiaryScreenState();
}

class _DiaryScreenState extends ConsumerState<DiaryScreen> {
  bool _week = false;

  @override
  void initState() {
    super.initState();
    // Once per screen open: no date, no numbers.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) trackDiaryDayViewed(ref);
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final day = ref.watch(diaryDayProvider(widget.date));
    final settings = ref.watch(goalSettingsProvider).value;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.diaryTitle),
        actions: [
          IconButton(
            tooltip: l10n.searchTitle,
            icon: const Icon(Icons.search_rounded),
            onPressed: () => context.push('/search'),
          ),
          if (settings != null) EyeToggle(settings: settings),
          if (day.value != null && !_week) DayMenu(day: day.value!),
        ],
      ),
      floatingActionButton: day.value == null || _week
          ? null
          : FloatingActionButton.extended(
              key: DiaryScreen.addFabKey,
              icon: const Icon(Icons.add_rounded),
              label: Text(l10n.diaryAdd),
              onPressed: () => addFood(context, ref, day.value!),
            ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
              SnTokens.space4,
              SnTokens.space2,
              SnTokens.space4,
              0,
            ),
            child: SegmentedButton<bool>(
              segments: [
                ButtonSegment(value: false, label: Text(l10n.diaryViewDay)),
                ButtonSegment(value: true, label: Text(l10n.diaryWeekTitle)),
              ],
              selected: {_week},
              onSelectionChanged: (v) => setState(() => _week = v.single),
            ),
          ),
          Expanded(
            child: _week
                ? WeekView(end: widget.date)
                : _dayBody(context, day, settings, l10n),
          ),
        ],
      ),
    );
  }

  Widget _dayBody(
    BuildContext context,
    AsyncValue<DiaryDayOut> day,
    GoalSettingsOut? settings,
    AppLocalizations l10n,
  ) {
    return day.when(
      skipLoadingOnRefresh: false,
      loading: () => const SingleChildScrollView(
        padding: EdgeInsets.all(SnTokens.space4),
        child: LoadingSkeleton(card: true, lines: 4),
      ),
      error: (e, _) => Center(
        child: SingleChildScrollView(
          child: ErrorState(
            message: localizedErrorCode(
              l10n,
              e is DiaryFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(diaryDayProvider(widget.date)),
          ),
        ),
      ),
      data: (d) => DiaryDayBody(day: d, date: widget.date, settings: settings),
    );
  }
}

/// Opens the add-food sheet, then the flow the user chose. The existing
/// search, scanner and label screens log through the portion sheet, which
/// reads [diaryAddContextProvider]; it is cleared when they are done.
Future<void> addFood(
  BuildContext context,
  WidgetRef ref,
  DiaryDayOut day, {
  String? slotId,
}) async {
  final next = await showAddFoodSheet(context, day: day, slotId: slotId);
  if (next == null || !context.mounted) return;
  final path = switch (next) {
    AddFoodNext.search => '/search',
    AddFoodNext.barcode => '/scan',
    AddFoodNext.label => '/scan/label',
  };
  await context.push(path);
  ref.read(diaryAddContextProvider.notifier).clear();
}

/// The loaded day: header, rings (or the reason there are none), the slots
/// and the footer.
class DiaryDayBody extends ConsumerWidget {
  const DiaryDayBody({
    super.key,
    required this.day,
    required this.date,
    required this.settings,
  });

  final DiaryDayOut day;
  final String? date;
  final GoalSettingsOut? settings;

  Future<void> _toggleView(
    WidgetRef ref,
    GoalSettingsOutSummaryView now,
  ) async {
    try {
      await ref
          .read(targetsRepositoryProvider)
          .setDisplay(
            DisplayIn(
              summaryView: now == GoalSettingsOutSummaryView.remaining
                  ? DisplayInSummaryView.consumed
                  : DisplayInSummaryView.remaining,
            ),
          );
      refreshTargets(ref);
    } on TargetsFailure {
      // The chip stays as it was; the next tap tries again.
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final view = settings?.summaryView ?? GoalSettingsOutSummaryView.remaining;
    final status = day.targetsStatus;
    final anyEntries = day.slots.any((s) => s.entries.isNotEmpty);
    final hidden = day.numbersHidden.energy || day.numbersHidden.macros;
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(mealSyncProvider).flush();
        ref.read(mealsRevisionProvider.notifier).bump();
      },
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space4,
          SnTokens.space2,
          SnTokens.space4,
          SnTokens.space6,
        ),
        children: [
          const SyncBanner(),
          const PickSlotAgain(),
          DayHeader(day: day),
          if (day.partialLogged)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: Align(
                alignment: AlignmentDirectional.centerStart,
                child: Chip(
                  key: DiaryScreen.partialKey,
                  label: Text(l10n.diaryPartialBadge),
                ),
              ),
            ),
          if (status == DiaryDayOutTargetsStatus.consentRequired)
            _ConsentCard(
              onGranted: () {
                ref.invalidate(consentStateProvider);
                refreshTargets(ref);
              },
            )
          else if (status == DiaryDayOutTargetsStatus.none)
            const _NoGuide()
          else if (status != DiaryDayOutTargetsStatus.ready &&
              day.targets != null)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: Text(statusMessage(l10n, day.targets!) ?? ''),
            ),
          DiaryRings(
            day: day,
            view: view,
            onToggleView: settings == null
                ? null
                : () => _toggleView(ref, view),
          ),
          Padding(
            key: DiaryScreen.bandsKey,
            padding: const EdgeInsets.only(top: SnTokens.space2),
            child: Wrap(
              spacing: SnTokens.space3,
              runSpacing: SnTokens.space2,
              children: [
                for (final (n, b) in [
                  (SummaryNutrient.sugars, day.limitsBands.sugarG),
                  (SummaryNutrient.salt, day.limitsBands.saltG),
                ])
                  Row(
                    key: DiaryScreen.bandKey(n.name),
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        nutrientLabel(l10n, n),
                        style: Theme.of(
                          context,
                        ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
                      ),
                      const SizedBox(width: SnTokens.space2),
                      // The API's band as sent; an unrecognised one is unknown.
                      BandChip(band: Band.fromApi(b)),
                    ],
                  ),
              ],
            ),
          ),
          if (hidden)
            Padding(
              key: DiaryScreen.hiddenNoteKey,
              padding: const EdgeInsets.only(top: SnTokens.space2),
              child: Text(
                l10n.diaryHiddenNumbers,
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(color: c.textSecondary),
              ),
            ),
          const SizedBox(height: SnTokens.space3),
          if (!anyEntries)
            Padding(
              key: DiaryScreen.emptyKey,
              padding: const EdgeInsets.symmetric(vertical: SnTokens.space2),
              child: Text(l10n.diaryEmptyDay),
            ),
          for (final slot in day.slots)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space2),
              child: SlotSection(
                slot: slot,
                onAdd: slot.archived
                    ? null
                    : () => addFood(context, ref, day, slotId: slot.slotId),
                menu: PopupMenuButton<String>(
                  key: SlotSection.menuKey(slot.slotId),
                  onSelected: (_) => showCopySheet(
                    context,
                    fromDate: dateKey(day.date),
                    toDate: dateKey(day.today),
                    fromSlotId: slot.slotId,
                    askTarget: true,
                  ),
                  itemBuilder: (_) => [
                    PopupMenuItem(
                      value: 'copy',
                      child: Text(l10n.diaryCopyMeal),
                    ),
                  ],
                ),
                pending: [
                  for (final r in pendingForSlot(
                    ref.watch(pendingEntriesProvider).value ??
                        const <PendingMeal>[],
                    day,
                    slot,
                    fallbackSlotId: ref
                        .watch(mealSlotsProvider)
                        .value
                        ?.suggestedSlotId,
                  ))
                    PendingEntryTile(row: r),
                ],
                onEntryMove: (e) async {
                  final moved = await showMoveEntrySheet(context, e);
                  if (moved == true) ref.invalidate(diaryDayProvider(date));
                },
                onEntryTap: (e) async {
                  final changed = await showEditEntrySheet(context, e);
                  if (changed == true) {
                    ref.invalidate(diaryDayProvider(date));
                  }
                },
              ),
            ),
          const SizedBox(height: SnTokens.space3),
          // Wherever a target or a remainder shows: the disclaimer and the
          // clinician-review note.
          if (status == DiaryDayOutTargetsStatus.ready)
            const Align(
              key: DiaryScreen.pendingReviewKey,
              child: PendingReviewNote(),
            ),
          DisclaimerFooter(text: l10n.diaryDisclaimer),
        ],
      ),
    );
  }
}

class _NoGuide extends StatelessWidget {
  const _NoGuide();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Card(
      key: DiaryScreen.noGuideKey,
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.diaryNoGuide),
            const SizedBox(height: SnTokens.space2),
            FilledButton(
              key: DiaryScreen.setupKey,
              onPressed: () => context.push('/guide/setup'),
              child: Text(l10n.targetsSetupCta),
            ),
          ],
        ),
      ),
    );
  }
}

/// The inline card when `health_data` is missing: a grant button, never a
/// redirect.
class _ConsentCard extends StatelessWidget {
  const _ConsentCard({required this.onGranted});

  final VoidCallback onGranted;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Card(
      key: DiaryScreen.consentKey,
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.diaryTargetsConsent),
            const SizedBox(height: SnTokens.space2),
            FilledButton(
              key: DiaryScreen.consentButtonKey,
              onPressed: () async {
                if (await showConsentSheet(context)) onGranted();
              },
              child: Text(l10n.consentAgree),
            ),
          ],
        ),
      ),
    );
  }
}
