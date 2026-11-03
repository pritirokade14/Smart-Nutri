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
import '../../meals/presentation/log_meal_sheet.dart';
import '../../scan/domain/number_text.dart';
import '../data/product_discovery_repository.dart';
import 'discovery_routes.dart';
import 'product_discovery_providers.dart';

/// The API's `member_status` as a status string; null when not sent.
String? memberStatusString(MemberStatus? s) => switch (s) {
  null => null,
  MemberStatus.ok => 'ok',
  MemberStatus.caution => 'caution',
  MemberStatus.avoid => 'avoid',
  _ => 'unknown',
};

/// "Healthier options": products of the same kind with a strictly better
/// Nutri-Score (calculated by SmartNutri), for the picked member, exactly as
/// the API ranked them. A product the API marks `avoid` for that member is
/// never offered.
class AlternativesSection extends ConsumerStatefulWidget {
  const AlternativesSection({
    super.key,
    required this.product,
    required this.verdicts,
  });

  final ProductRef product;

  /// The members, from the analysis (for the picker and the names only).
  final List<VerdictOut> verdicts;

  @override
  ConsumerState<AlternativesSection> createState() =>
      _AlternativesSectionState();
}

class _AlternativesSectionState extends ConsumerState<AlternativesSection> {
  late String? _memberId = _initialMember();

  String? _initialMember() {
    final vs = widget.verdicts;
    if (vs.isEmpty) return null;
    return vs.firstWhere((v) => v.isPrimary, orElse: () => vs.first).memberId;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final query = (product: widget.product, memberId: _memberId);
    final result = ref.watch(alternativesProvider(query));
    final member = [
      for (final v in widget.verdicts)
        if (v.memberId == _memberId) v,
    ].firstOrNull;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.alternativesTitle,
          subtitle: l10n.alternativesSubtitle,
          icon: Icons.swap_horiz_rounded,
        ),
        if (widget.verdicts.length > 1)
          Padding(
            padding: const EdgeInsets.only(bottom: SnTokens.space3),
            child: Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space2,
              children: [
                for (final v in widget.verdicts)
                  ChoiceChip(
                    label: Text(memberLabel(l10n, v)),
                    selected: v.memberId == _memberId,
                    onSelected: (_) => setState(() => _memberId = v.memberId),
                  ),
              ],
            ),
          ),
        result.when(
          skipLoadingOnRefresh: false,
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is DiscoveryFailure ? e.code : null,
            ),
            icon: Icons.cloud_off_rounded,
            onRetry: () => ref.invalidate(alternativesProvider(query)),
          ),
          data: (out) {
            final items = [
              for (final a in out.items)
                // Defence in depth (Ruling M1): never offer an avoid.
                if (_memberId == null || a.memberStatus != MemberStatus.avoid)
                  a,
            ];
            if (items.isEmpty) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: SnTokens.space2),
                child: Text(_reasonText(l10n, out.reason)),
              );
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final a in items)
                  _AlternativeTile(
                    item: a,
                    source: widget.product,
                    memberId: _memberId,
                    memberName: member == null
                        ? null
                        : memberLabel(l10n, member),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }

  static String _reasonText(AppLocalizations l10n, AlternativesOutReason r) =>
      switch (r) {
        AlternativesOutReason.noCategory => l10n.alternativesReasonNoCategory,
        AlternativesOutReason.sourceUngraded =>
          l10n.alternativesReasonSourceUngraded,
        _ => l10n.alternativesReasonNoBetterFound,
      };
}

class _AlternativeTile extends StatelessWidget {
  const _AlternativeTile({
    required this.item,
    required this.source,
    required this.memberId,
    required this.memberName,
  });

  final AlternativeOut item;
  final ProductRef source;
  final String? memberId;
  final String? memberName;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final a = item;
    final ref = (productId: a.productId, barcode: a.barcode);
    final status = memberStatusString(a.memberStatus);
    final brand = a.brand;
    final sugars = a.sugarsG;
    final barcode = a.barcode;
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      child: InkWell(
        borderRadius: BorderRadius.circular(SnTokens.radiusLg),
        onTap: () => context.push(resultLocation(ref)),
        child: Padding(
          padding: const EdgeInsets.all(SnTokens.space3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  NutriScoreBadge(grade: a.grade.json),
                  const SizedBox(width: SnTokens.space3),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(a.name, style: theme.textTheme.titleMedium),
                        if (brand != null)
                          Text(
                            brand,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: c.textSecondary,
                            ),
                          ),
                        if (sugars != null)
                          Text(
                            l10n.alternativesSugars(formatForDisplay(sugars)),
                            style: theme.textTheme.bodySmall,
                          ),
                      ],
                    ),
                  ),
                ],
              ),
              if (status != null && memberName != null) ...[
                const SizedBox(height: SnTokens.space2),
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        l10n.alternativesForMember(memberName!),
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                    const SizedBox(width: SnTokens.space2),
                    VerdictBadge(status: status),
                  ],
                ),
              ],
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: TextButton.icon(
                  icon: const Icon(Icons.compare_arrows_rounded),
                  label: Text(l10n.alternativesCompare),
                  onPressed: () => context.push(
                    compareLocation(source, ref, memberId: memberId),
                  ),
                ),
              ),
              if (a.attribution != null && barcode != null)
                OffAttribution(barcode: barcode),
            ],
          ),
        ),
      ),
    );
  }
}
