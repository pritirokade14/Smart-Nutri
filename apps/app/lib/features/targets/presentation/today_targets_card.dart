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
import '../../history/presentation/history_providers.dart';
import '../../home/presentation/cards/card_frame.dart';
import '../../meals/domain/meal_summary.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart';
import '../data/targets_repository.dart';
import '../domain/targets_format.dart';
import 'eye_toggle.dart';
import 'guide_result_step.dart';
import 'targets_explanation.dart';
import 'targets_providers.dart';

/// Home's "Today" card: the API's daily targets as rows (never rings), with
/// what was eaten for calories and protein from `meals_summary`. The card
/// never computes a target, a remainder or a flag.
class TodayTargetsCard extends ConsumerWidget {
  const TodayTargetsCard({super.key});

  static const setupKey = Key('today-targets-setup');
  static const skipKey = Key('today-targets-skip');
  static const consentKey = Key('today-targets-consent');
  static const consentButtonKey = Key('today-targets-consent-grant');
  static Key rowKey(String name) => Key('today-row-$name');
  static const incompleteKey = Key('today-incomplete');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final targets = ref.watch(todayTargetsProvider);
    final settingsState = ref.watch(goalSettingsProvider);
    final settings = settingsState.value;
    // With health data withdrawn the settings cannot be read, but the eye
    // toggle only needs the terms, so it stays.
    final settingsErr = settingsState.error;
    final consentLost =
        (settingsErr is TargetsFailure && settingsErr.isConsentRequired) ||
        (targets.error is TargetsFailure &&
            (targets.error as TargetsFailure).isConsentRequired);
    final dismissed = ref.watch(todayTargetsDismissedProvider);
    if (dismissed && targets.value?.status == TargetsOutStatus.none) {
      return const SizedBox.shrink();
    }
    return HomeCardFrame(
      title: l10n.homeCardsTodayTargetsTitle,
      icon: Icons.today_rounded,
      trailing: settings == null && !consentLost
          ? null
          : EyeToggle(settings: settings),
      child: targets.when(
        loading: () => const LoadingSkeleton(lines: 3),
        error: (e, _) {
          if (e is TargetsFailure && e.isConsentRequired) {
            return _ConsentCard(
              onGranted: () {
                ref.invalidate(consentStateProvider);
                refreshTargets(ref);
              },
            );
          }
          return ErrorState(
            message: localizedErrorCode(
              l10n,
              e is TargetsFailure ? e.code : null,
            ),
            onRetry: () => refreshTargets(ref),
          );
        },
        data: (t) => _Body(targets: t),
      ),
    );
  }
}

/// The inline card when `health_data` is missing: a grant button, never a
/// redirect to a consent screen.
class _ConsentCard extends StatelessWidget {
  const _ConsentCard({required this.onGranted});

  final VoidCallback onGranted;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      key: TodayTargetsCard.consentKey,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(l10n.diaryTargetsConsent),
        const SizedBox(height: SnTokens.space2),
        FilledButton(
          key: TodayTargetsCard.consentButtonKey,
          onPressed: () async {
            if (await showConsentSheet(context)) onGranted();
          },
          child: Text(l10n.consentAgree),
        ),
      ],
    );
  }
}

class _Body extends ConsumerWidget {
  const _Body({required this.targets});

  final TargetsOut targets;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final t = targets;
    switch (t.status) {
      case TargetsOutStatus.none:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton(
              key: TodayTargetsCard.setupKey,
              onPressed: () => context.push('/guide/setup'),
              child: Text(l10n.targetsSetupCta),
            ),
            TextButton(
              key: TodayTargetsCard.skipKey,
              onPressed: () =>
                  ref.read(todayTargetsDismissedProvider.notifier).dismiss(),
              child: Text(l10n.targetsSkip),
            ),
          ],
        );
      case TargetsOutStatus.ready:
        return _Ready(targets: t);
      default:
        final message = statusMessage(l10n, t);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (message != null) Text(message),
            if (t.status == TargetsOutStatus.needsBodyData)
              TextButton(
                onPressed: () => context.push('/guide/setup'),
                child: Text(l10n.targetsSetupCta),
              ),
            DisclaimerFooter(text: l10n.diaryDisclaimer),
          ],
        );
    }
  }
}

class _Ready extends ConsumerWidget {
  const _Ready({required this.targets});

  final TargetsOut targets;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final t = targets;
    final primary = ref
        .watch(membersProvider)
        .value
        ?.where((m) => m.isPrimary)
        .firstOrNull;
    final MealSummary? summary = primary == null
        ? null
        : ref
              .watch(
                mealSummaryProvider((
                  memberId: primary.id,
                  period: SummaryPeriod.day,
                )),
              )
              .value;
    num? eaten(SummaryNutrient n) =>
        summary == null || summary.isHidden(n) ? null : summary.totals[n];
    bool incomplete(SummaryNutrient n) =>
        summary != null &&
        summary.anyLogged &&
        !summary.isHidden(n) &&
        summary.incomplete[n];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (t.energyKcal != null)
          _TargetLine(
            name: 'energy',
            label: l10n.targetsEnergy,
            target: kcalText(l10n, t.energyKcal!),
            eaten: eaten(SummaryNutrient.kcal) == null
                ? null
                : kcalText(l10n, eaten(SummaryNutrient.kcal)!),
            incomplete: incomplete(SummaryNutrient.kcal),
          ),
        if (t.proteinG != null)
          _TargetLine(
            name: 'protein',
            label: l10n.targetsProtein,
            target: gramsText(l10n, t.proteinG!),
            eaten: eaten(SummaryNutrient.protein) == null
                ? null
                : gramsText(l10n, eaten(SummaryNutrient.protein)!),
            incomplete: incomplete(SummaryNutrient.protein),
          ),
        if (t.fatG != null)
          _TargetLine(
            name: 'fat',
            label: l10n.targetsFat,
            target: gramsText(l10n, t.fatG!),
          ),
        if (t.carbsG != null)
          _TargetLine(
            name: 'carbs',
            label: l10n.targetsCarbs,
            target: gramsText(l10n, t.carbsG!),
          ),
        if (t.numbersHidden.energy || t.numbersHidden.macros)
          Padding(
            key: TargetRows.hiddenKey,
            padding: const EdgeInsets.only(top: SnTokens.space1),
            child: Text(
              l10n.diaryHiddenNumbers,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SnColors.of(context).textSecondary,
              ),
            ),
          ),
        const SizedBox(height: SnTokens.space2),
        const PendingReviewNote(),
        DisclaimerFooter(text: l10n.diaryDisclaimer),
      ],
    );
  }
}

/// One target row. Eaten, when known, reads "{eaten} of {target}" in the
/// neutral text colour whatever the amount (no red, no "X over": a
/// remainder is the API's, not the app's). An incomplete eaten total is the
/// grey chip, not a number.
class _TargetLine extends StatelessWidget {
  const _TargetLine({
    required this.name,
    required this.label,
    required this.target,
    this.eaten,
    this.incomplete = false,
  });

  final String name;
  final String label;
  final String target;
  final String? eaten;
  final bool incomplete;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final showEaten = eaten != null && !incomplete;
    return Padding(
      key: TodayTargetsCard.rowKey(name),
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(label, style: theme.textTheme.titleSmall)),
              Text(
                showEaten ? l10n.diaryOfTarget(eaten!, target) : target,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: c.textPrimary,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ],
          ),
          if (incomplete)
            Container(
              key: TodayTargetsCard.incompleteKey,
              margin: const EdgeInsets.only(top: SnTokens.space1),
              padding: const EdgeInsets.symmetric(
                horizontal: SnTokens.space2,
                vertical: SnTokens.space1,
              ),
              decoration: BoxDecoration(
                color: c.muted,
                borderRadius: BorderRadius.circular(SnTokens.radiusFull),
              ),
              child: Text(
                l10n.diaryIncomplete,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
