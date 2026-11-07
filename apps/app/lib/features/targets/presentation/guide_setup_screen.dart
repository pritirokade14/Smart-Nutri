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
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../members/presentation/members_providers.dart';
import '../domain/targets_format.dart';
import 'about_you_step.dart';
import 'activity_step.dart';
import 'goal_step.dart';
import 'guide_actions.dart';
import 'guide_draft.dart';
import 'guide_result_step.dart';
import 'numbers_choice.dart';

/// The API's message for an out-of-range body fat %.
String bodyFatMessage(AppLocalizations l10n, Map<String, Object?> details) =>
    l10n.targetsBodyFatOutOfRange(
      formatDecimal((details['max'] as num?) ?? 70),
      formatDecimal((details['min'] as num?) ?? 3),
    );

/// The message for a target weight below the API's minimum.
String targetWeightMessage(
  AppLocalizations l10n,
  String? code,
  Map<String, Object?> details,
) {
  final min = details['min_kg'];
  return min is num
      ? l10n.targetsTargetWeightTooLow(formatDecimal(min))
      : localizedErrorCode(l10n, code);
}

/// The five setup steps (spec 7.1): intro, about you, activity, goal, and
/// your guide. Nothing is saved until Save on the last step.
class GuideSetupScreen extends ConsumerStatefulWidget {
  const GuideSetupScreen({super.key, this.fromWelcome = false});

  /// Opened right after onboarding (`?from=welcome`).
  final bool fromWelcome;

  static const nextKey = Key('guide-next');
  static const backKey = Key('guide-back');
  static const skipKey = Key('guide-skip');
  static const saveKey = Key('guide-save');
  static const unusualKey = Key('guide-unusual-confirm');
  static const editAnswersKey = Key('guide-edit-answers');
  static const errorKey = Key('guide-error');

  @override
  ConsumerState<GuideSetupScreen> createState() => _GuideSetupScreenState();
}

class _GuideSetupScreenState extends ConsumerState<GuideSetupScreen> {
  final _draft = GuideDraft();
  int _step = 0;
  bool _loaded = false;
  bool _busy = false;
  TargetsOut? _preview;
  String? _error;
  String? _notice;
  String? _bodyFatError;
  String? _targetWeightError;
  bool _unusualOk = false;

  @override
  void initState() {
    super.initState();
    // The buttons depend on the answers.
    _draft.addListener(_onDraft);
  }

  void _onDraft() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _draft.dispose();
    super.dispose();
  }

  void _ensureLoaded() {
    if (_loaded) return;
    final members = ref.read(membersProvider).value;
    final primary = members?.where((m) => m.isPrimary).firstOrNull;
    if (primary == null) return;
    _loaded = true;
    _draft.load(primary, null);
  }

  /// Runs a preview. False when the flow cannot go on: a declined consent,
  /// or an error shown here (body fat errors go back to "About you").
  Future<bool> _runPreview() async {
    final l10n = AppLocalizations.of(context);
    // No preview until the pregnancy question is answered.
    if (!_draft.pregnancyAnswered) return true;
    setState(() {
      _busy = true;
      _error = null;
      _bodyFatError = null;
      _targetWeightError = null;
    });
    var out = await previewGuide(context, ref, _draft);
    // An underweight "lose" is offered as staying the same (neutral copy).
    if (out.code == 'goal_not_allowed_underweight' && mounted) {
      _draft
        ..direction = 'maintain'
        ..ratePct = null
        ..notify();
      _notice = l10n.targetsUnderweight;
      out = await previewGuide(context, ref, _draft);
    }
    if (!mounted) return false;
    setState(() {
      _busy = false;
      _preview = out.targets ?? _preview;
      _unusualOk = false;
    });
    if (out.ok) {
      _draft
        ..missing = {...out.targets!.missingFields}
        ..notify();
      return true;
    }
    if (out.cancelled) return false;
    setState(() {
      switch (out.code) {
        case 'body_fat_out_of_range':
          _bodyFatError = bodyFatMessage(l10n, out.details);
          _step = 1;
        case 'target_weight_too_low':
          _targetWeightError = targetWeightMessage(l10n, out.code, out.details);
        default:
          _error = localizedErrorCode(l10n, out.code);
      }
    });
    return false;
  }

  Future<void> _next() async {
    // The goal step needs the pace options, the last step the numbers.
    if ((_step == 2 || _step == 3) && !await _runPreview()) return;
    if (mounted) setState(() => _step++);
  }

  Future<void> _save() async {
    final l10n = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    final out = await saveGuide(context, ref, _draft);
    if (!mounted) return;
    setState(() => _busy = false);
    if (out.ok) {
      context.go('/home');
      return;
    }
    if (out.cancelled) return;
    setState(() {
      if (out.code == 'body_fat_out_of_range') {
        _bodyFatError = bodyFatMessage(l10n, out.details);
        _step = 1;
      } else {
        _error = localizedErrorCode(l10n, out.code);
      }
    });
  }

  bool get _canContinue {
    if (_busy) return false;
    return switch (_step) {
      2 => _draft.activity != null,
      3 => _draft.pregnancyAnswered && !_draft.hasUnreadableNumber,
      _ => !_draft.hasUnreadableNumber,
    };
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    // Load the consent states so a missing consent is asked for up front.
    ref.watch(consentStateProvider);
    final members = ref.watch(membersProvider);
    _ensureLoaded();
    final titles = [
      l10n.targetsTitle,
      l10n.targetsStepAbout,
      l10n.targetsStepActivity,
      l10n.targetsStepGoal,
      l10n.targetsStepGuide,
    ];
    final Widget body;
    if (!_loaded) {
      body = members.hasError
          ? ErrorState(
              message: localizedErrorCode(l10n, null),
              onRetry: () => ref.invalidate(membersProvider),
            )
          : const LoadingSkeleton(lines: 5);
    } else {
      body = _stepBody(context, l10n);
    }
    return Scaffold(
      appBar: AppBar(
        title: Text(titles[_step]),
        leading: _step == 0
            ? null
            : IconButton(
                key: GuideSetupScreen.backKey,
                icon: const Icon(Icons.arrow_back_rounded),
                tooltip: MaterialLocalizations.of(context).backButtonTooltip,
                onPressed: _busy ? null : () => setState(() => _step--),
              ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(SnTokens.space4),
          children: [
            body,
            if (_error case final message?) ...[
              const SizedBox(height: SnTokens.space3),
              InlineErrorBanner(
                key: GuideSetupScreen.errorKey,
                message: message,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _stepBody(BuildContext context, AppLocalizations l10n) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final next = PrimaryButton(
      buttonKey: GuideSetupScreen.nextKey,
      label: l10n.userTypesContinue,
      busy: _busy,
      onPressed: _canContinue ? _next : null,
    );
    switch (_step) {
      case 0:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.targetsIntroTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: SnTokens.space2),
            Text(
              l10n.targetsIntroBody,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space4),
            ListenableBuilder(
              listenable: _draft,
              builder: (_, _) => NumbersChoice(
                value: _draft.numbersDisplay,
                onChanged: (v) {
                  _draft.numbersDisplay = v;
                  _draft.notify();
                },
              ),
            ),
            const SizedBox(height: SnTokens.space4),
            next,
            TextButton(
              key: GuideSetupScreen.skipKey,
              onPressed: () => context.go('/home'),
              child: Text(l10n.targetsSkip),
            ),
          ],
        );
      case 1:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AboutYouStep(draft: _draft, bodyFatError: _bodyFatError),
            const SizedBox(height: SnTokens.space4),
            next,
          ],
        );
      case 2:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ActivityStep(draft: _draft),
            const SizedBox(height: SnTokens.space2),
            next,
          ],
        );
      case 3:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GoalStep(
              draft: _draft,
              preview: _preview,
              notice: _notice,
              targetWeightError: _targetWeightError,
              onChanged: () {
                _runPreview();
              },
            ),
            const SizedBox(height: SnTokens.space4),
            next,
          ],
        );
      default:
        final t = _preview;
        if (t == null) return const LoadingSkeleton(lines: 4);
        final unusual = t.unusualFields
            .map((f) => missingFieldLabel(l10n, f))
            .join(', ');
        final needsData = t.status == TargetsOutStatus.needsBodyData;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GuideResultStep(targets: t),
            if (t.unusualFields.isNotEmpty)
              CheckboxListTile(
                key: GuideSetupScreen.unusualKey,
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                value: _unusualOk,
                onChanged: (v) => setState(() => _unusualOk = v ?? false),
                title: Text(l10n.targetsUnusualConfirm(unusual)),
              ),
            const SizedBox(height: SnTokens.space3),
            if (needsData)
              PrimaryButton(
                buttonKey: GuideSetupScreen.editAnswersKey,
                label: l10n.targetsStepAbout,
                onPressed: () => setState(() => _step = 1),
              )
            else
              PrimaryButton(
                buttonKey: GuideSetupScreen.saveKey,
                label: l10n.targetsSave,
                busy: _busy,
                onPressed: _busy || (t.unusualFields.isNotEmpty && !_unusualOk)
                    ? null
                    : _save,
              ),
          ],
        );
    }
  }
}
