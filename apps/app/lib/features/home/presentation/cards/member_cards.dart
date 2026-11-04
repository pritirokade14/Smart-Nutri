import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/l10n/app_localizations.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/theme/tokens.g.dart';
import '../../../../shared/widgets/states.dart';
import '../../../history/presentation/history_providers.dart';
import '../../../history/presentation/history_screen.dart' show memberOutLabel;
import '../../../members/data/members_repository.dart';
import '../../../members/presentation/member_labels.dart';
import '../../../members/presentation/members_providers.dart';
import 'card_frame.dart';

String _membersError(AppLocalizations l10n, Object e) =>
    localizedErrorCode(l10n, e is MembersFailure ? e.code : null);

/// Who has which allergy (`members_list`). Unknown is never marked safe.
/// With no allergies (allergy mode only) it offers to add them.
class AllergyCheckCard extends ConsumerWidget {
  const AllergyCheckCard({super.key});

  static const addKey = Key('home-allergy-add');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    return HomeCardFrame(
      title: l10n.homeCardsAllergyCheckTitle,
      icon: Icons.no_food_outlined,
      child: members.when(
        loading: () => const LoadingSkeleton(lines: 2),
        error: (e, _) => ErrorState(
          message: _membersError(l10n, e),
          onRetry: () => ref.invalidate(membersProvider),
        ),
        data: (list) {
          final withAllergies = [
            for (final m in list)
              if (m.allergens.isNotEmpty) m,
          ];
          if (withAllergies.isEmpty) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CardBody(l10n.homeCardsAllergyCheckNone),
                TextButton.icon(
                  key: addKey,
                  icon: const Icon(Icons.add_rounded),
                  label: Text(l10n.homeCardsAllergyCheckAddCta),
                  onPressed: () => context.go('/family'),
                ),
              ],
            );
          }
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final m in withAllergies)
                Padding(
                  padding: const EdgeInsets.only(bottom: SnTokens.space1),
                  child: Text(
                    l10n.homeCardsAllergyCheckMemberLine(
                      [
                        for (final a in m.allergens) allergenLabel(l10n, a),
                      ].join(', '),
                      memberOutLabel(l10n, m),
                    ),
                  ),
                ),
              const SizedBox(height: SnTokens.space1),
              CardBody(l10n.homeCardsAllergyCheckUnknownNote),
            ],
          );
        },
      ),
    );
  }
}

/// The family at a glance, with "Add member".
class FamilyStripCard extends ConsumerWidget {
  const FamilyStripCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final members = ref.watch(membersProvider);
    return HomeCardFrame(
      title: l10n.homeCardsFamilyStripTitle,
      icon: Icons.groups_rounded,
      action: TextButton.icon(
        icon: const Icon(Icons.person_add_alt_1_rounded),
        label: Text(l10n.homeCardsFamilyStripAdd),
        onPressed: () => context.push('/family/new'),
      ),
      child: members.when(
        loading: () => const LoadingSkeleton(lines: 1),
        error: (e, _) => ErrorState(
          message: _membersError(l10n, e),
          onRetry: () => ref.invalidate(membersProvider),
        ),
        data: (list) => Wrap(
          spacing: SnTokens.space2,
          runSpacing: SnTokens.space2,
          children: [
            for (final m in list)
              ActionChip(
                avatar: const Icon(Icons.person_outline_rounded),
                label: Text(memberOutLabel(l10n, m)),
                onPressed: () => context.push('/family/${m.id}'),
              ),
          ],
        ),
      ),
    );
  }
}

/// Items logged for the family this week: counts only.
class WeeklyFamilyCard extends ConsumerWidget {
  const WeeklyFamilyCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return HomeCardFrame(
      title: l10n.homeCardsWeeklyFamilyTitle,
      icon: Icons.date_range_rounded,
      child: ref
          .watch(weekCountsProvider)
          .when(
            loading: () => const LoadingSkeleton(lines: 1),
            error: (e, _) => ErrorState(
              message: localizedErrorCode(l10n, null),
              onRetry: () => ref.invalidate(weekCountsProvider),
            ),
            data: (w) =>
                CardBody(l10n.homeCardsWeeklyFamilyBody('${w.logged}')),
          ),
    );
  }
}

/// A call to switch on ingredient alerts for the account holder.
class CustomAlertsSetupCard extends ConsumerWidget {
  const CustomAlertsSetupCard({super.key});

  static const ctaKey = Key('home-alerts-setup');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final primary = ref
        .watch(membersProvider)
        .value
        ?.where((m) => m.isPrimary)
        .firstOrNull;
    return HomeCardFrame(
      title: l10n.homeCardsCustomAlertsSetupTitle,
      icon: Icons.notifications_active_outlined,
      action: TextButton.icon(
        key: ctaKey,
        icon: const Icon(Icons.tune_rounded),
        label: Text(l10n.homeCardsCustomAlertsSetupCta),
        onPressed: () => primary == null
            ? context.go('/family')
            : context.push('/family/${primary.id}'),
      ),
      child: CardBody(l10n.homeCardsCustomAlertsSetupBody),
    );
  }
}
