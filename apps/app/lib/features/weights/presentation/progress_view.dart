import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/states.dart';
import '../../diary/presentation/diary_providers.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart'
    show consentGranted, consentStateProvider;
import '../../targets/domain/targets_format.dart';
import '../../targets/presentation/flag_notes.dart';
import '../../targets/presentation/targets_explanation.dart';
import '../../targets/presentation/targets_providers.dart';
import '../data/weights_repository.dart';
import 'weigh_in_sheet.dart';
import 'weight_chart.dart';
import 'weight_list.dart';
import 'weights_providers.dart';

/// The weight log as a screen of its own (Profile, "Weight").
class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(AppLocalizations.of(context).weightTitle)),
    body: const ProgressView(),
  );
}

/// The Progress tab: the weigh-ins as dots, the trend as a line, the weekly
/// rate and the projection, all exactly as the API sent them. Nothing is
/// worked out here. No streaks, no rating.
class ProgressView extends ConsumerStatefulWidget {
  const ProgressView({super.key});

  static const consentKey = Key('progress-consent');
  static const consentButtonKey = Key('progress-consent-grant');
  static const deleteAllKey = Key('progress-delete-all');
  static const deleteAllConfirmKey = Key('progress-delete-all-confirm');
  static const addKey = Key('progress-add');
  static const emptyKey = Key('progress-empty');
  static const rateKey = Key('progress-weekly-rate');
  static const projectionKey = Key('progress-projection');
  static const noProjectionKey = Key('progress-no-projection');
  static const rapidLossKey = Key('progress-rapid-loss');
  static const pendingReviewKey = Key('progress-pending-review');
  static Key rangeKey(int days) => Key('progress-range-$days');
  static Key flagKey(String flag) => Key('progress-flag-$flag');

  @override
  ConsumerState<ProgressView> createState() => _ProgressViewState();
}

class _ProgressViewState extends ConsumerState<ProgressView> {
  Days _days = Days.value90;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final consent = consentGranted(
      ref.watch(consentStateProvider).value,
      'health_data',
    );
    final padding = const EdgeInsets.fromLTRB(
      SnTokens.space4,
      SnTokens.space2,
      SnTokens.space4,
      SnTokens.space6,
    );
    // Without health data consent: the consent card and nothing else.
    if (consent == false) {
      return ListView(
        padding: padding,
        children: [_ConsentCard(onGranted: _granted)],
      );
    }
    // Keeps the diary's today (the default weigh-in day) loaded.
    ref.watch(diaryDayProvider(null));
    final trend = ref.watch(weightTrendProvider(_days));
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(weighInSyncProvider).flush();
        refreshWeights(ref);
      },
      child: ListView(
        padding: padding,
        children: [
          Wrap(
            spacing: SnTokens.space2,
            children: [
              for (final (d, label) in [
                (Days.value30, l10n.weightRange30),
                (Days.value90, l10n.weightRange90),
                (Days.value365, l10n.weightRange365),
              ])
                ChoiceChip(
                  key: ProgressView.rangeKey(d.json!),
                  label: Text(label),
                  selected: _days == d,
                  onSelected: (_) => setState(() => _days = d),
                ),
            ],
          ),
          const SizedBox(height: SnTokens.space3),
          trend.when(
            skipLoadingOnRefresh: false,
            loading: () => const LoadingSkeleton(card: true, lines: 4),
            error: (e, _) {
              final code = e is WeightsFailure ? e.code : null;
              if (code == 'consent_required') {
                return _ConsentCard(onGranted: _granted);
              }
              return ErrorState(
                message: localizedErrorCode(l10n, code),
                onRetry: () => ref.invalidate(weightTrendProvider(_days)),
              );
            },
            data: (t) => _Body(trend: t),
          ),
          const SizedBox(height: SnTokens.space3),
          DisclaimerFooter(text: l10n.diaryDisclaimer),
        ],
      ),
    );
  }

  void _granted() {
    ref.invalidate(consentStateProvider);
    ref.invalidate(weightTrendProvider);
    ref.invalidate(weightListProvider);
  }
}

class _Body extends ConsumerWidget {
  const _Body({required this.trend});

  final WeightTrendOut trend;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final list = ref.watch(weightListProvider).value;
    final pending =
        ref.watch(pendingWeighInsProvider).value ?? const <PendingWeighIn>[];
    final targets = ref.watch(todayTargetsProvider).value;
    final rate = trend.weeklyRate;
    final projection = trend.projection;
    final hidden = trend.numbersHidden;
    final empty = trend.points.isEmpty && pending.isEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (trend.points.isNotEmpty) ...[
          WeightChart(trend: trend),
          const SizedBox(height: SnTokens.space2),
          Text(
            l10n.weightTrend,
            style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
          ),
        ] else if (empty)
          Padding(
            key: ProgressView.emptyKey,
            padding: const EdgeInsets.symmetric(vertical: SnTokens.space3),
            child: Text(l10n.weightEmpty),
          ),
        const SizedBox(height: SnTokens.space3),
        PrimaryButton(
          buttonKey: ProgressView.addKey,
          label: l10n.weightAdd,
          icon: Icons.add_rounded,
          onPressed: () => showWeighInSheet(context),
        ),
        const SizedBox(height: SnTokens.space3),
        if (rate != null)
          Text(
            l10n.weightWeeklyRate(
              formatDecimal(rate.kg),
              formatDecimal(rate.pctBw),
            ),
            key: ProgressView.rateKey,
            style: theme.textTheme.titleSmall,
          ),
        // A projection only when the API says it is ready; otherwise its
        // reason, in plain words.
        if (trend.projectionReason == WeightTrendOutProjectionReason.ready &&
            projection != null &&
            projection.targetKg != null &&
            projection.date != null)
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space1),
            child: Text(
              l10n.weightProjection(
                (DateFormat.yMMMd(
                  l10n.localeName,
                )..useNativeDigits = false).format(projection.date!),
                formatDecimal(projection.targetKg!),
              ),
              key: ProgressView.projectionKey,
            ),
          )
        else if (_noProjection(l10n, trend.projectionReason) case final m?)
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space1),
            child: Text(
              m,
              key: ProgressView.noProjectionKey,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
        if (trend.flags.contains('rapid_loss'))
          _Note(
            key: ProgressView.rapidLossKey,
            // Hidden numbers: the same note without the percentage.
            text: hidden || trend.rapidLossPct == null
                ? l10n.weightRapidLossHidden
                : l10n.weightRapidLoss(formatDecimal(trend.rapidLossPct!)),
          ),
        // The taper and goal-reached notes come from today's targets.
        if (targets != null)
          for (final f in const ['taper_active', 'goal_weight_reached'])
            if (targets.flags.contains(f))
              if (flagMessage(l10n, f, targets) case final m?)
                _Note(key: ProgressView.flagKey(f), text: m),
        const SizedBox(height: SnTokens.space3),
        WeightList(
          items: list?.items ?? const [],
          pending: pending,
          // Offline (no list yet) a queued number is not shown: the user may
          // have hidden numbers and the app cannot tell.
          numbersHidden: list?.numbersHidden ?? hidden,
        ),
        const SizedBox(height: SnTokens.space2),
        const Align(
          key: ProgressView.pendingReviewKey,
          child: PendingReviewNote(),
        ),
      ],
    );
  }

  static String? _noProjection(
    AppLocalizations l10n,
    WeightTrendOutProjectionReason r,
  ) => switch (r) {
    WeightTrendOutProjectionReason.tooFewWeighIns =>
      l10n.weightNoProjectionTooFewWeighIns,
    WeightTrendOutProjectionReason.movingAway =>
      l10n.weightNoProjectionMovingAway,
    WeightTrendOutProjectionReason.noTarget => l10n.weightNoProjectionNoTarget,
    WeightTrendOutProjectionReason.tooFar => l10n.weightNoProjectionTooFar,
    WeightTrendOutProjectionReason.reached => l10n.weightNoProjectionReached,
    _ => null,
  };
}

/// A neutral information note (never the danger or a verdict colour).
class _Note extends StatelessWidget {
  const _Note({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Container(
      margin: const EdgeInsets.only(top: SnTokens.space2),
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: c.muted,
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.info_outline_rounded,
            size: SnTokens.fontSizeMd,
            color: c.textSecondary,
          ),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Text(
              text,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: c.textPrimary),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConsentCard extends ConsumerWidget {
  const _ConsentCard({required this.onGranted});

  final VoidCallback onGranted;

  /// Erasing never needs consent: delete every weigh-in, after a confirm.
  Future<void> _deleteAll(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(l10n.weightDeleteAllConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(material.cancelButtonLabel),
          ),
          TextButton(
            key: ProgressView.deleteAllConfirmKey,
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.weightDeleteAll),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(weightsRepositoryProvider).deleteAll();
      refreshWeights(ref);
      messenger.showSnackBar(SnackBar(content: Text(l10n.weightDeleteAllDone)));
    } on WeightsFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return Card(
      key: ProgressView.consentKey,
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.weightConsent),
            const SizedBox(height: SnTokens.space2),
            FilledButton(
              key: ProgressView.consentButtonKey,
              onPressed: () async {
                if (await showConsentSheet(context)) onGranted();
              },
              child: Text(l10n.consentAgree),
            ),
            TextButton(
              key: ProgressView.deleteAllKey,
              onPressed: () => _deleteAll(context, ref),
              child: Text(l10n.weightDeleteAll),
            ),
          ],
        ),
      ),
    );
  }
}
