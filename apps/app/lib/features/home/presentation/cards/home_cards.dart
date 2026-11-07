import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/l10n/app_localizations.dart';
import '../../../../shared/widgets/section_header.dart';
import '../../../../shared/widgets/states.dart';
import '../../../members/presentation/members_providers.dart';
import '../../../modes/mode_layouts.dart';
import '../../../modes/mode_providers.dart';
import '../../../targets/presentation/today_targets_card.dart';
import 'card_frame.dart';
import 'member_cards.dart';
import 'today_cards.dart';

/// Home's cards for the focused mode, in the layout's order, with
/// `allergy_check` first whenever a member has an allergen (P9-R7). Cards
/// render API values only.
class HomeCards extends ConsumerWidget {
  const HomeCards({super.key});

  static Key cardKey(String card) => Key('home-card-$card');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(activeModeProvider);
    final members = ref.watch(membersProvider).value ?? const [];
    final cards = homeCardsFor(
      mode,
      anyMemberHasAllergens: members.any((m) => m.allergens.isNotEmpty),
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final card in cards)
          KeyedSubtree(key: cardKey(card), child: _card(context, card)),
      ],
    );
  }

  static Widget _card(BuildContext context, String card) {
    final l10n = AppLocalizations.of(context);
    return switch (card) {
      'allergy_check' => const AllergyCheckCard(),
      'today_sugar_salt' => const TodaySugarSaltCard(),
      'today_targets' => const TodayTargetsCard(),
      'today_protein' => const TodayProteinCard(),
      'protein_swaps' => HomeCardFrame(
        title: l10n.homeCardsProteinSwapsTitle,
        icon: Icons.swap_horiz_rounded,
        action: TextButton.icon(
          icon: const Icon(Icons.fitness_center_rounded),
          label: Text(l10n.homeCardsProteinSwapsCta),
          onPressed: () => context.go('/protein'),
        ),
        child: const SizedBox.shrink(),
      ),
      'protein_claims_tip' => HomeCardFrame(
        title: l10n.homeCardsProteinClaimsTipTitle,
        icon: Icons.fact_check_outlined,
        child: CardBody(l10n.homeCardsProteinClaimsTipBody),
      ),
      'claims_tip' => HomeCardFrame(
        title: l10n.homeCardsClaimsTipTitle,
        icon: Icons.fact_check_outlined,
        child: CardBody(l10n.homeCardsClaimsTipBody),
      ),
      'not_covered' => HomeCardFrame(
        title: l10n.homeCardsNotCoveredTitle,
        icon: Icons.info_outline_rounded,
        child: CardBody(l10n.homeCardsNotCoveredBody),
      ),
      'unknown_explainer' => HomeCardFrame(
        title: l10n.homeCardsUnknownExplainerTitle,
        icon: Icons.help_outline_rounded,
        child: CardBody(l10n.homeCardsUnknownExplainerBody),
      ),
      'family_strip' => const FamilyStripCard(),
      'weekly_family' => const WeeklyFamilyCard(),
      'custom_alerts_setup' => const CustomAlertsSetupCard(),
      'recent_scans' => const RecentScansSection(),
      _ => const SizedBox.shrink(),
    };
  }
}

/// The recent-scans list (always last). There is no stored recent list yet,
/// so it shows its empty state, as before.
class RecentScansSection extends StatelessWidget {
  const RecentScansSection({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.homeRecentTitle,
          icon: Icons.receipt_long_rounded,
        ),
        Card(
          child: EmptyState(
            icon: Icons.shopping_basket_outlined,
            title: l10n.homeRecentEmptyTitle,
            body: l10n.homeRecentEmptyBody,
          ),
        ),
      ],
    );
  }
}
