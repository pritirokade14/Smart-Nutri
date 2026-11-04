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
import '../../../shared/widgets/nutri_score_chip.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../../shared/widgets/verdict_badge.dart';
import '../../history/presentation/history_providers.dart';
import '../../history/presentation/history_screen.dart' show memberOutLabel;
import '../../meals/data/meals_repository.dart';
import '../../product/data/product_discovery_repository.dart';
import '../../product/presentation/alternatives_section.dart';
import '../../product/presentation/discovery_routes.dart';
import '../../product/presentation/product_discovery_providers.dart';
import '../../scan/domain/number_text.dart';

/// Higher-protein options for what the member logged today, and a search
/// ranked by protein. Lists come from the API (`sort=protein`, the member's
/// id), which never offers an `avoid` for that member or a supplement.
class ProteinSwaps extends ConsumerWidget {
  const ProteinSwaps({super.key, required this.member});

  final MemberOut member;

  static Key optionsKey(String mealId) => Key('protein-swaps-$mealId');
  static const searchKey = Key('protein-search');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: SnTokens.space4),
        SectionHeader(
          title: l10n.proteinSwapsTitle,
          icon: Icons.swap_horiz_rounded,
        ),
        Text(l10n.historyToday, style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: SnTokens.space2),
        ref
            .watch(mealsListProvider(member.id))
            .when(
              skipLoadingOnRefresh: false,
              loading: () => const LoadingSkeleton(lines: 2),
              error: (e, _) => ErrorState(
                message: localizedErrorCode(
                  l10n,
                  e is MealsFailure ? e.code : null,
                ),
                onRetry: () => ref.invalidate(mealsListProvider(member.id)),
              ),
              data: (meals) {
                final now = DateTime.now();
                final today = [
                  for (final m in meals)
                    if (_sameDay(m.eatenAt.toLocal(), now)) m,
                ];
                if (today.isEmpty) return Text(l10n.historyEmpty);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    for (final m in today) _MealSwaps(meal: m, member: member),
                  ],
                );
              },
            ),
        const SizedBox(height: SnTokens.space4),
        _ProteinSearch(member: member),
      ],
    );
  }

  static bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;
}

class _MealSwaps extends ConsumerStatefulWidget {
  const _MealSwaps({required this.meal, required this.member});

  final MealOut meal;
  final MemberOut member;

  @override
  ConsumerState<_MealSwaps> createState() => _MealSwapsState();
}

class _MealSwapsState extends ConsumerState<_MealSwaps> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final meal = widget.meal;
    final ProductRef? product = meal.productId != null
        ? (productId: meal.productId, barcode: null)
        : meal.barcode != null
        ? (productId: null, barcode: meal.barcode)
        : null;
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space3),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              meal.productName,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            if (product != null)
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: TextButton.icon(
                  key: ProteinSwaps.optionsKey(meal.id),
                  icon: Icon(
                    _open
                        ? Icons.expand_less_rounded
                        : Icons.fitness_center_rounded,
                  ),
                  label: Text(l10n.proteinSwapsTitle),
                  onPressed: () => setState(() => _open = !_open),
                ),
              ),
            if (_open && product != null) _options(product),
          ],
        ),
      ),
    );
  }

  Widget _options(ProductRef product) {
    final l10n = AppLocalizations.of(context);
    final query = (
      product: product,
      memberId: widget.member.id,
      sort: AlternativesSort.protein,
    );
    return ref
        .watch(alternativesProvider(query))
        .when(
          skipLoadingOnRefresh: false,
          loading: () => const LoadingSkeleton(lines: 2),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is DiscoveryFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(alternativesProvider(query)),
          ),
          data: (out) {
            final items = [
              for (final a in out.items)
                // Defence in depth: never offer an avoid for this member.
                if (a.memberStatus != MemberStatus.avoid) a,
            ];
            if (items.isEmpty) {
              return Text(switch (out.reason) {
                AlternativesOutReason.sourceSupplement =>
                  l10n.alternativesReasonSourceSupplement,
                AlternativesOutReason.sourceProteinUnknown =>
                  l10n.alternativesReasonSourceProteinUnknown,
                _ => l10n.proteinSwapsEmpty,
              });
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final a in items)
                  AlternativeTile(
                    item: a,
                    source: product,
                    memberId: widget.member.id,
                    memberName: memberOutLabel(l10n, widget.member),
                  ),
                Text(
                  l10n.nutriscoreCalculatedBy,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SnColors.of(context).textSecondary,
                  ),
                ),
              ],
            );
          },
        );
  }
}

/// A search ranked by protein for the member.
class _ProteinSearch extends ConsumerStatefulWidget {
  const _ProteinSearch({required this.member});

  final MemberOut member;

  @override
  ConsumerState<_ProteinSearch> createState() => _ProteinSearchState();
}

class _ProteinSearchState extends ConsumerState<_ProteinSearch> {
  final _controller = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final q = _query;
    final query = (q: q, sort: SearchSort.protein, memberId: widget.member.id);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          key: ProteinSwaps.searchKey,
          controller: _controller,
          maxLength: searchMaxLength,
          textInputAction: TextInputAction.search,
          onSubmitted: (text) => setState(() => _query = text.trim()),
          decoration: InputDecoration(
            hintText: l10n.searchPlaceholder,
            prefixIcon: const Icon(Icons.search_rounded),
            counterText: '',
          ),
        ),
        const SizedBox(height: SnTokens.space2),
        if (q.isEmpty)
          const SizedBox.shrink()
        else if (q.length < searchMinLength)
          Text(l10n.searchTooShort)
        else
          ref
              .watch(productSearchProvider(query))
              .when(
                skipLoadingOnRefresh: false,
                loading: () => const LoadingSkeleton(lines: 3),
                error: (e, _) => ErrorState(
                  message: localizedErrorCode(
                    l10n,
                    e is DiscoveryFailure ? e.code : null,
                  ),
                  onRetry: () => ref.invalidate(productSearchProvider(query)),
                ),
                data: (hits) => hits.isEmpty
                    ? Text(l10n.searchNoResults)
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (final h in hits)
                            Card(
                              margin: const EdgeInsets.only(
                                bottom: SnTokens.space2,
                              ),
                              child: ListTile(
                                leading: NutriScoreBadge(grade: h.grade?.json),
                                title: Text(h.name),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    if (h.proteinPer100kcal case final p?)
                                      Text(
                                        '${l10n.proteinPer100kcal}: '
                                        '${formatForDisplay(p)}',
                                      ),
                                    if (memberStatusString(h.memberStatus)
                                        case final s?)
                                      VerdictBadge(status: s),
                                    if (h.attribution != null &&
                                        h.barcode != null)
                                      OffAttribution(barcode: h.barcode!),
                                  ],
                                ),
                                onTap: () => context.push(
                                  resultLocation((
                                    productId: h.productId,
                                    barcode: h.barcode,
                                  )),
                                ),
                              ),
                            ),
                          Text(
                            l10n.nutriscoreCalculatedBy,
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ),
              ),
      ],
    );
  }
}
