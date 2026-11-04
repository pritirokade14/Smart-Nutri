import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../history/presentation/history_providers.dart';
import '../../history/presentation/history_screen.dart' show memberOutLabel;
import '../../history/presentation/summary_display.dart';
import '../../meals/data/meals_repository.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/members_providers.dart';
import 'protein_progress.dart';

/// The member whose protein is shown; null is the account holder.
class ProteinMember extends Notifier<String?> {
  @override
  String? build() => null;

  void select(String memberId) => state = memberId;
}

final proteinMemberProvider = NotifierProvider<ProteinMember, String?>(
  ProteinMember.new,
);

String _failureText(AppLocalizations l10n, Object e) =>
    localizedErrorCode(l10n, switch (e) {
      MealsFailure(:final code) => code,
      MembersFailure(:final code) => code,
      _ => null,
    });

/// The Protein tab: today's protein for a member against their daily guide
/// (from `meals_summary`), with the no-target and kidney notes. Information,
/// not medical advice; the guide never changes a verdict.
class ProteinScreen extends ConsumerWidget {
  const ProteinScreen({super.key});

  static Key memberKey(String id) => Key('protein-member-$id');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.proteinTitle)),
      body: members.when(
        skipLoadingOnRefresh: false,
        loading: () => const SingleChildScrollView(
          padding: EdgeInsets.all(SnTokens.space4),
          child: LoadingSkeleton(card: true, lines: 4),
        ),
        error: (e, _) => Center(
          child: SingleChildScrollView(
            child: ErrorState(
              message: _failureText(l10n, e),
              onRetry: () => ref.invalidate(membersProvider),
            ),
          ),
        ),
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: EmptyState(
                icon: Icons.fitness_center_outlined,
                title: l10n.historyEmpty,
              ),
            );
          }
          final picked = ref.watch(proteinMemberProvider);
          final member =
              list.where((m) => m.id == picked).firstOrNull ??
              list.where((m) => m.isPrimary).firstOrNull ??
              list.first;
          return _ProteinBody(members: list, member: member);
        },
      ),
    );
  }
}

class _ProteinBody extends ConsumerWidget {
  const _ProteinBody({required this.members, required this.member});

  final List<MemberOut> members;
  final MemberOut member;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final day = (memberId: member.id, period: SummaryPeriod.day);
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space4,
        SnTokens.space2,
        SnTokens.space4,
        SnTokens.space6,
      ),
      children: [
        if (members.length > 1) ...[
          Wrap(
            spacing: SnTokens.space2,
            runSpacing: SnTokens.space2,
            children: [
              for (final m in members)
                ChoiceChip(
                  key: ProteinScreen.memberKey(m.id),
                  label: Text(memberOutLabel(l10n, m)),
                  selected: m.id == member.id,
                  onSelected: (_) =>
                      ref.read(proteinMemberProvider.notifier).select(m.id),
                ),
            ],
          ),
          const SizedBox(height: SnTokens.space3),
        ],
        Card(
          child: Padding(
            padding: const EdgeInsets.all(SnTokens.space4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SectionHeader(
                  title: l10n.summaryTitleDay,
                  icon: Icons.today_rounded,
                ),
                ref
                    .watch(mealSummaryProvider(day))
                    .when(
                      skipLoadingOnRefresh: false,
                      loading: () => const LoadingSkeleton(lines: 2),
                      error: (e, _) => ErrorState(
                        message: _failureText(l10n, e),
                        onRetry: () => ref.invalidate(mealSummaryProvider(day)),
                      ),
                      data: (s) => ProteinProgress(
                        summary: s,
                        onAddDetails: () =>
                            context.push('/family/${member.id}'),
                      ),
                    ),
                SummaryNote(text: l10n.proteinKidneyNote),
              ],
            ),
          ),
        ),
        ...proteinScreenExtras(context, ref, member),
        const DisclaimerFooter(),
      ],
    );
  }
}

/// Sections added below the progress card (Task 11: swaps and search).
List<Widget> proteinScreenExtras(
  BuildContext context,
  WidgetRef ref,
  MemberOut member,
) => const [];
