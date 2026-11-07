import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../members/presentation/consent_sheet.dart';
import '../../members/presentation/members_providers.dart';
import '../data/targets_repository.dart';
import 'about_you_step.dart';
import 'activity_step.dart';
import 'goal_step.dart';
import 'guide_actions.dart';
import 'guide_draft.dart';
import 'guide_result_step.dart';
import 'guide_setup_screen.dart';
import 'numbers_choice.dart';
import 'targets_providers.dart';

/// "Diary and daily guide" under Profile: the setup answers as editable
/// sections, the Numbers choice, and "Reset daily guide".
class GuideSettingsScreen extends ConsumerWidget {
  const GuideSettingsScreen({super.key});

  static const setupKey = Key('guide-settings-setup');
  static const consentKey = Key('guide-settings-consent');
  static const saveKey = Key('guide-settings-save');
  static const resetKey = Key('guide-settings-reset');
  static const resetConfirmKey = Key('guide-settings-reset-confirm');
  static const unusualKey = Key('guide-settings-unusual');
  static const errorKey = Key('guide-settings-error');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    ref.watch(consentStateProvider);
    final members = ref.watch(membersProvider);
    final settings = ref.watch(goalSettingsProvider);
    final primary = members.value?.where((m) => m.isPrimary).firstOrNull;
    final Widget body;
    if (settings.hasError) {
      final e = settings.error;
      body = e is TargetsFailure && e.isConsentRequired
          ? _ConsentNote(onGranted: () => ref.invalidate(goalSettingsProvider))
          : ErrorState(
              message: localizedErrorCode(
                l10n,
                e is TargetsFailure ? e.code : null,
              ),
              onRetry: () => ref.invalidate(goalSettingsProvider),
            );
    } else if (primary == null || settings.isLoading) {
      body = const LoadingSkeleton(lines: 5);
    } else if (settings.value == null) {
      body = Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(l10n.targetsIntroBody),
          const SizedBox(height: SnTokens.space3),
          PrimaryButton(
            buttonKey: setupKey,
            label: l10n.targetsSetupCta,
            onPressed: () => context.push('/guide/setup'),
          ),
        ],
      );
    } else {
      body = _SettingsForm(
        key: ValueKey(settings.value!.updatedAt),
        primary: primary,
        stored: settings.value!,
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text(l10n.settingsDiaryTitle)),
      body: ListView(
        padding: const EdgeInsets.all(SnTokens.space4),
        children: [body],
      ),
    );
  }
}

/// The card shown instead of a redirect when `health_data` is missing.
class _ConsentNote extends StatelessWidget {
  const _ConsentNote({required this.onGranted});

  final VoidCallback onGranted;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      key: GuideSettingsScreen.consentKey,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(l10n.diaryTargetsConsent),
        const SizedBox(height: SnTokens.space3),
        PrimaryButton(
          label: l10n.consentAgree,
          onPressed: () async {
            if (await showConsentSheet(context)) onGranted();
          },
        ),
      ],
    );
  }
}

class _SettingsForm extends ConsumerStatefulWidget {
  const _SettingsForm({super.key, required this.primary, required this.stored});

  final MemberOut primary;
  final GoalSettingsOut stored;

  @override
  ConsumerState<_SettingsForm> createState() => _SettingsFormState();
}

class _SettingsFormState extends ConsumerState<_SettingsForm> {
  final _draft = GuideDraft();
  bool _busy = false;
  TargetsOut? _preview;
  String? _error;
  String? _bodyFatError;
  String? _targetWeightError;
  bool _unusualAsked = false;
  bool _unusualOk = false;
  String _unusual = '';

  @override
  void initState() {
    super.initState();
    _draft.load(widget.primary, widget.stored);
    _draft.addListener(_onDraft);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _refreshPreview();
    });
  }

  void _onDraft() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _draft.dispose();
    super.dispose();
  }

  /// Pace options for the current answers (`targets_preview`).
  Future<TargetsOut?> _refreshPreview() async {
    final l10n = AppLocalizations.of(context);
    setState(() {
      _error = null;
      _bodyFatError = null;
      _targetWeightError = null;
    });
    final out = await previewGuide(context, ref, _draft);
    if (!mounted) return null;
    setState(() {
      _preview = out.targets ?? _preview;
      if (out.ok || out.cancelled) return;
      switch (out.code) {
        case 'body_fat_out_of_range':
          _bodyFatError = bodyFatMessage(l10n, out.details);
        case 'target_weight_too_low':
          _targetWeightError = targetWeightMessage(l10n, out.code, out.details);
        default:
          _error = localizedErrorCode(l10n, out.code);
      }
    });
    return out.targets;
  }

  Future<void> _setNumbers(String value) async {
    final l10n = AppLocalizations.of(context);
    final previous = _draft.numbersDisplay;
    _draft
      ..numbersDisplay = value
      ..notify();
    try {
      await ref
          .read(targetsRepositoryProvider)
          .setDisplay(
            DisplayIn(numbersDisplay: DisplayInNumbersDisplay.fromJson(value)),
          );
      if (mounted) refreshTargets(ref);
    } on TargetsFailure catch (e) {
      _draft
        ..numbersDisplay = previous
        ..notify();
      if (mounted) setState(() => _error = localizedErrorCode(l10n, e.code));
    }
  }

  Future<void> _save() async {
    final l10n = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _error = null;
      _bodyFatError = null;
    });
    final t = await _refreshPreview();
    if (!mounted) return;
    if (t == null) {
      setState(() => _busy = false);
      return;
    }
    if (t.unusualFields.isNotEmpty && !_unusualOk) {
      setState(() {
        _busy = false;
        _unusualAsked = true;
        _unusual = t.unusualFields
            .map((f) => missingFieldLabel(l10n, f))
            .join(', ');
      });
      return;
    }
    final out = await saveGuide(context, ref, _draft);
    if (!mounted) return;
    setState(() => _busy = false);
    if (out.ok) {
      ScaffoldMessenger.maybeOf(
        context,
      )?.showSnackBar(SnackBar(content: Text(l10n.membersSaved)));
      return;
    }
    if (out.cancelled) return;
    setState(() {
      if (out.code == 'body_fat_out_of_range') {
        _bodyFatError = bodyFatMessage(l10n, out.details);
      } else {
        _error = localizedErrorCode(l10n, out.code);
      }
    });
  }

  Future<void> _reset() async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Text(l10n.settingsDiaryResetConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l10n.commonCancel),
          ),
          TextButton(
            key: GuideSettingsScreen.resetConfirmKey,
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l10n.settingsDiaryReset),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ref.read(targetsRepositoryProvider).reset();
      if (mounted) refreshTargets(ref);
    } on TargetsFailure catch (e) {
      if (mounted) setState(() => _error = localizedErrorCode(l10n, e.code));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ListenableBuilder(
          listenable: _draft,
          builder: (_, _) => NumbersChoice(
            value: _draft.numbersDisplay,
            onChanged: _setNumbers,
          ),
        ),
        SectionHeader(
          title: l10n.targetsStepAbout,
          icon: Icons.person_outline_rounded,
        ),
        AboutYouStep(draft: _draft, bodyFatError: _bodyFatError),
        SectionHeader(
          title: l10n.targetsStepActivity,
          icon: Icons.directions_walk_rounded,
        ),
        ActivityStep(draft: _draft),
        SectionHeader(title: l10n.targetsStepGoal, icon: Icons.flag_outlined),
        GoalStep(
          draft: _draft,
          preview: _preview,
          targetWeightError: _targetWeightError,
          onChanged: _refreshPreview,
        ),
        if (_unusualAsked)
          CheckboxListTile(
            key: GuideSettingsScreen.unusualKey,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _unusualOk,
            onChanged: (v) => setState(() => _unusualOk = v ?? false),
            title: Text(l10n.targetsUnusualConfirm(_unusual)),
          ),
        if (_error case final message?) ...[
          const SizedBox(height: SnTokens.space3),
          InlineErrorBanner(
            key: GuideSettingsScreen.errorKey,
            message: message,
          ),
        ],
        const SizedBox(height: SnTokens.space4),
        PrimaryButton(
          buttonKey: GuideSettingsScreen.saveKey,
          label: l10n.targetsSave,
          busy: _busy,
          onPressed: _draft.activity == null || _draft.hasUnreadableNumber
              ? null
              : _save,
        ),
        const SizedBox(height: SnTokens.space2),
        TextButton.icon(
          key: GuideSettingsScreen.resetKey,
          icon: const Icon(Icons.restart_alt_rounded),
          label: Text(l10n.settingsDiaryReset),
          onPressed: _busy ? null : _reset,
        ),
        DisclaimerFooter(text: l10n.diaryDisclaimer),
      ],
    );
  }
}
