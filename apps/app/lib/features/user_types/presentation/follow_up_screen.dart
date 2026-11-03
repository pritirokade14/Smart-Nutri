import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../members/domain/member.dart';
import '../../members/presentation/member_labels.dart';
import '../domain/user_types.dart';
import 'user_type_labels.dart';
import 'user_types_flow.dart';
import 'user_types_providers.dart';

/// At most one short question per chosen type, in priority order. Nothing
/// here changes a member: answers are stored with the types, and any profile
/// change is offered on the review screen for the user to confirm.
class FollowUpScreen extends ConsumerStatefulWidget {
  const FollowUpScreen({super.key, this.edit = false});

  final bool edit;

  static const nextKey = Key('follow-up-next');
  static const addMemberKey = Key('follow-up-add-member');
  static Key chipKey(String group, String code) =>
      Key('follow-up-$group-$code');

  @override
  ConsumerState<FollowUpScreen> createState() => _FollowUpScreenState();
}

class _FollowUpScreenState extends ConsumerState<FollowUpScreen> {
  int _step = 0;
  bool _busy = false;

  void _set(FollowUpAnswers answers) =>
      ref.read(userTypesDraftProvider.notifier).setAnswers(answers);

  Future<void> _next(int steps) async {
    if (_step < steps - 1) {
      setState(() => _step++);
      return;
    }
    setState(() => _busy = true);
    final saved = await saveUserTypes(context, ref, edit: widget.edit);
    if (!mounted) return;
    setState(() => _busy = false);
    if (!saved && ref.read(userTypesDraftProvider).types.isEmpty) {
      // Declining consent left nothing: back to the picker.
      if (context.canPop()) context.pop();
    }
  }

  void _back() {
    if (_step > 0) {
      setState(() => _step--);
    } else if (context.canPop()) {
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final draft = ref.watch(userTypesDraftProvider);
    final steps = followUpTypes(draft.types);
    if (steps.isEmpty) {
      return Scaffold(appBar: AppBar());
    }
    final step = _step.clamp(0, steps.length - 1);
    final type = steps[step];
    return PopScope(
      canPop: step == 0,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _back();
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(userTypeTitle(l10n, type)),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(SnTokens.space1),
            child: LinearProgressIndicator(value: (step + 1) / steps.length),
          ),
        ),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(SnTokens.space4),
            children: [
              ..._questions(context, type, draft.answers),
              const SizedBox(height: SnTokens.space5),
              PrimaryButton(
                buttonKey: FollowUpScreen.nextKey,
                label: l10n.userTypesContinue,
                // Disabled, not spinning: a consent sheet may be open.
                onPressed: _busy ? null : () => _next(steps.length),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _questions(
    BuildContext context,
    String type,
    FollowUpAnswers a,
  ) {
    final l10n = AppLocalizations.of(context);
    List<String> toggled(List<String> list, String k, bool on) =>
        on ? [...list, k] : [...list.where((v) => v != k)];

    Widget multi(
      String group,
      List<String> keys,
      List<String> selected,
      String Function(String) label,
      void Function(List<String>) onChanged,
    ) => Wrap(
      spacing: SnTokens.space2,
      runSpacing: SnTokens.space2,
      children: [
        for (final k in keys)
          FilterChip(
            key: FollowUpScreen.chipKey(group, k),
            label: Text(label(k)),
            selected: selected.contains(k),
            onSelected: _busy
                ? null
                : (on) => onChanged(toggled(selected, k, on)),
          ),
      ],
    );

    Widget single(
      String group,
      List<String> keys,
      String? selected,
      String Function(String) label,
      void Function(String?) onChanged,
    ) => Wrap(
      spacing: SnTokens.space2,
      runSpacing: SnTokens.space2,
      children: [
        for (final k in keys)
          ChoiceChip(
            key: FollowUpScreen.chipKey(group, k),
            label: Text(label(k)),
            selected: selected == k,
            onSelected: _busy ? null : (on) => onChanged(on ? k : null),
          ),
      ],
    );

    return switch (type) {
      'health_condition' => [
        _Question(l10n.userTypesFollowUpHealthConditionQuestion),
        multi(
          'conditions',
          conditionKeys,
          a.conditions,
          (k) => conditionLabel(l10n, k),
          (v) => _set(a.copyWith(conditions: v)),
        ),
        const SizedBox(height: SnTokens.space4),
        _Note(
          title: l10n.userTypesNotCoveredTitle,
          body: l10n.userTypesNotCoveredBody,
        ),
      ],
      'family' => [
        _Question(l10n.userTypesFollowUpFamilyQuestion),
        multi(
          'family',
          familyWithKeys,
          a.familyWith,
          (k) => familyWithLabel(l10n, k),
          (v) => _set(a.copyWith(familyWith: v)),
        ),
        const SizedBox(height: SnTokens.space4),
        OutlinedButton.icon(
          key: FollowUpScreen.addMemberKey,
          icon: const Icon(Icons.person_add_alt_1_rounded),
          label: Text(l10n.membersAdd),
          onPressed: _busy ? null : () => context.push('/family/new'),
        ),
      ],
      'gym' => [
        _Question(l10n.userTypesFollowUpGymQuestion),
        single(
          'gym',
          gymGoalKeys,
          a.gymGoal,
          (k) => gymGoalLabel(l10n, k),
          (v) => _set(a.copyWith(gymGoal: () => v)),
        ),
      ],
      'allergy_diet' => [
        _Question(l10n.userTypesFollowUpAllergyDietAllergensQuestion),
        multi(
          'allergens',
          canonicalAllergens,
          a.allergens,
          (k) => allergenLabel(l10n, k),
          (v) => _set(a.copyWith(allergens: v)),
        ),
        const SizedBox(height: SnTokens.space4),
        _Question(l10n.userTypesFollowUpAllergyDietDietQuestion),
        single(
          'diet',
          dietKeys,
          a.diet,
          (k) => dietLabel(l10n, k),
          (v) => _set(a.copyWith(diet: () => v)),
        ),
      ],
      'eat_better' => [
        _Question(l10n.userTypesFollowUpEatBetterQuestion),
        Text(
          l10n.userTypesFollowUpEatBetterHint,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: SnColors.of(context).textSecondary,
          ),
        ),
        const SizedBox(height: SnTokens.space2),
        multi(
          'alerts',
          customAlertKeys,
          a.alerts,
          (k) => alertLabel(l10n, k),
          (v) => _set(a.copyWith(alerts: v)),
        ),
      ],
      _ => const [],
    };
  }
}

class _Question extends StatelessWidget {
  const _Question(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: SnTokens.space3),
    child: Text(text, style: Theme.of(context).textTheme.titleLarge),
  );
}

class _Note extends StatelessWidget {
  const _Note({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: c.muted,
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
        border: Border.all(color: c.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded, color: c.textSecondary),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: theme.textTheme.titleSmall),
                Text(body, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
