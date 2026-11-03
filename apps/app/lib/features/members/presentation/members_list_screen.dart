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
import '../data/members_repository.dart';
import 'member_labels.dart';
import 'members_providers.dart';

/// The API's member limit (`members/service.py` MAX_MEMBERS).
const maxMembers = 10;

/// Family tab: every member, the account holder first, as the API lists
/// them. Tap one to edit; add up to [maxMembers].
class MembersListScreen extends ConsumerWidget {
  const MembersListScreen({super.key});

  static const addKey = Key('members-add');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    final consents = ref.watch(consentStateProvider).value;
    final health = consents
        ?.where((s) => s.purpose == consentPurposeHealthData)
        .firstOrNull;
    // Agreed once, now withdrawn (or out of date): saved data still counts.
    final withdrawn =
        health != null && !health.granted && health.version != null;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.membersTitle)),
      body: members.when(
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
                e is MembersFailure ? e.code : null,
              ),
              onRetry: () => ref.invalidate(membersProvider),
            ),
          ),
        ),
        data: (list) => RefreshIndicator(
          onRefresh: () => ref.refresh(membersProvider.future),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(
              SnTokens.space4,
              SnTokens.space2,
              SnTokens.space4,
              SnTokens.space6,
            ),
            children: [
              Text(
                l10n.familyBody,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: SnColors.of(context).textSecondary,
                ),
              ),
              const SizedBox(height: SnTokens.space3),
              if (withdrawn) ...[
                _Notice(text: l10n.membersConsentWithdrawnNotice),
                const SizedBox(height: SnTokens.space3),
              ],
              for (final m in list) _MemberTile(member: m),
              const SizedBox(height: SnTokens.space4),
              if (list.length >= maxMembers)
                _Notice(text: l10n.errorMemberLimit)
              else
                PrimaryButton(
                  buttonKey: addKey,
                  label: l10n.membersAdd,
                  icon: Icons.person_add_alt_1_rounded,
                  onPressed: () => context.push('/family/new'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MemberTile extends StatelessWidget {
  const _MemberTile({required this.member});

  final MemberOut member;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final m = member;
    final details = [
      relationLabel(l10n, m.relation.json),
      if (m.birthYear case final year?) l10n.membersBorn('$year'),
      dietLabel(l10n, m.diet.json ?? ''),
    ].where((s) => s.isNotEmpty).join(' · ');
    final health = [
      for (final a in m.allergens) allergenLabel(l10n, a),
      for (final cond in m.conditions)
        if (cond.json case final String code) conditionLabel(l10n, code),
    ];
    return Card(
      margin: const EdgeInsets.symmetric(vertical: SnTokens.space1),
      child: InkWell(
        borderRadius: BorderRadius.circular(SnTokens.radiusLg),
        onTap: () => context.push('/family/${m.id}'),
        child: Padding(
          padding: const EdgeInsets.all(SnTokens.space4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                backgroundColor: c.brandSoft,
                foregroundColor: c.brandStrong,
                child: Icon(
                  m.isPrimary ? Icons.person_rounded : Icons.face_rounded,
                ),
              ),
              const SizedBox(width: SnTokens.space3),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            m.name.isEmpty ? l10n.membersYouBadge : m.name,
                            style: theme.textTheme.titleMedium,
                          ),
                        ),
                        if (m.isPrimary && m.name.isNotEmpty) ...[
                          const SizedBox(width: SnTokens.space2),
                          _YouBadge(label: l10n.membersYouBadge),
                        ],
                      ],
                    ),
                    Text(
                      details,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                    if (health.isNotEmpty) ...[
                      const SizedBox(height: SnTokens.space1),
                      Text(health.join(', '), style: theme.textTheme.bodySmall),
                    ],
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: c.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

class _YouBadge extends StatelessWidget {
  const _YouBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space2,
        vertical: SnTokens.space1 / 2,
      ),
      decoration: BoxDecoration(
        color: c.brandSoft,
        borderRadius: BorderRadius.circular(SnTokens.radiusFull),
      ),
      child: Text(
        label,
        style: Theme.of(
          context,
        ).textTheme.labelSmall?.copyWith(color: c.brandStrong),
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Container(
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: c.muted,
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded, color: c.textSecondary),
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
