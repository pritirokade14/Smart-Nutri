import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/observability/analytics.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/nutri_score_chip.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../../../shared/widgets/verdict_badge.dart';
import '../../protein/presentation/price_per_scoop_section.dart';
import '../../scan/domain/number_text.dart';
import '../data/product_discovery_repository.dart';
import 'alternatives_section.dart';
import 'discovery_routes.dart';
import 'product_discovery_providers.dart';

/// Two products side by side, per 100 g/ml, with the "better" side of each
/// row exactly as the API decided it (`CompareOut.better`). Nothing is
/// compared on the device.
class CompareScreen extends ConsumerStatefulWidget {
  const CompareScreen({super.key, required this.a, this.b, this.memberId});

  final ProductRef? a;

  /// Null: the user still has to pick the second product.
  final ProductRef? b;
  final String? memberId;

  static const pickKey = Key('compare-pick-products');

  @override
  ConsumerState<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends ConsumerState<CompareScreen> {
  @override
  void initState() {
    super.initState();
    if (widget.a != null && widget.b != null) {
      // Event name only.
      ref.read(analyticsProvider).track('compare_opened');
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final a = widget.a;
    final b = widget.b;
    final Widget body;
    if (a == null) {
      // Opened from a tab or More: pick the products first.
      body = Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(SnTokens.space4),
          child: EmptyState(
            icon: Icons.compare_arrows_rounded,
            title: l10n.compareTitle,
            body: l10n.searchHint,
            action: PrimaryButton(
              buttonKey: CompareScreen.pickKey,
              label: l10n.searchTitle,
              icon: Icons.search_rounded,
              onPressed: () => context.push(searchLocation()),
            ),
          ),
        ),
      );
    } else if (b == null) {
      body = Center(
        child: Padding(
          padding: const EdgeInsets.all(SnTokens.space4),
          child: PrimaryButton(
            label: l10n.comparePickSecond,
            icon: Icons.search_rounded,
            onPressed: () => context.pushReplacement(
              searchLocation(compareWith: a, memberId: widget.memberId),
            ),
          ),
        ),
      );
    } else {
      final query = (a: a, b: b, memberId: widget.memberId);
      body = ref
          .watch(compareProvider(query))
          .when(
            skipLoadingOnRefresh: false,
            loading: () => const SingleChildScrollView(
              padding: EdgeInsets.all(SnTokens.space4),
              child: LoadingSkeleton(card: true, lines: 6),
            ),
            error: (e, _) => Center(
              child: SingleChildScrollView(
                child: ErrorState(
                  message: localizedErrorCode(
                    l10n,
                    e is DiscoveryFailure ? e.code : null,
                  ),
                  icon: Icons.cloud_off_rounded,
                  onRetry: () => ref.invalidate(compareProvider(query)),
                ),
              ),
            ),
            data: (out) => _CompareView(out: out),
          );
    }
    return Scaffold(
      appBar: AppBar(title: Text(l10n.compareTitle)),
      body: body,
    );
  }
}

typedef _Row = ({String key, String label, num? a, num? b, BetterSide better});

class _CompareView extends StatelessWidget {
  const _CompareView({required this.out});

  final CompareOut out;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final a = out.a.per100g;
    final b = out.b.per100g;
    final better = out.better;
    final rows = <_Row>[
      (
        key: 'energy_kcal',
        label: l10n.compareRowEnergyKcal,
        a: a.energyKcal,
        b: b.energyKcal,
        better: better.energyKcal,
      ),
      (
        key: 'sugars_g',
        label: l10n.compareRowSugarsG,
        a: a.sugarsG,
        b: b.sugarsG,
        better: better.sugarsG,
      ),
      (
        key: 'salt_g',
        label: l10n.compareRowSaltG,
        a: a.saltG,
        b: b.saltG,
        better: better.saltG,
      ),
      (
        key: 'sat_fat_g',
        label: l10n.compareRowSatFatG,
        a: a.satFatG,
        b: b.satFatG,
        better: better.satFatG,
      ),
      (
        key: 'protein_g',
        label: l10n.compareRowProteinG,
        a: a.proteinG,
        b: b.proteinG,
        better: better.proteinG,
      ),
      (
        key: 'fiber_g',
        label: l10n.compareRowFiberG,
        a: a.fiberG,
        b: b.fiberG,
        better: better.fiberG,
      ),
      // The protein guide's rows, per serving and per 100 kcal, as the API
      // calculated them (null without a serving size or energy).
      (
        key: 'protein_per_serving_g',
        label: l10n.proteinCompareProteinServing,
        a: out.a.proteinPerServingG,
        b: out.b.proteinPerServingG,
        better: better.proteinPerServingG,
      ),
      (
        key: 'protein_per_100kcal', // gitleaks:allow (a row id)
        label: l10n.proteinCompareProtein100kcal,
        a: out.a.proteinPer100kcal,
        b: out.b.proteinPer100kcal,
        better: better.proteinPer100kcal,
      ),
      (
        key: 'sugars_per_serving_g',
        label: l10n.proteinCompareSugar,
        a: out.a.sugarsPerServingG,
        b: out.b.sugarsPerServingG,
        better: better.sugarsPerServingG,
      ),
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.all(SnTokens.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(child: _SideHeader(side: out.a)),
                const SizedBox(width: SnTokens.space2),
                Expanded(child: _SideHeader(side: out.b)),
              ],
            ),
          ),
          const SizedBox(height: SnTokens.space3),
          _CompareRow(
            rowKey: 'grade',
            label: l10n.compareRowGrade,
            better: better.grade,
            a: NutriScoreBadge(grade: out.a.grade?.json),
            b: NutriScoreBadge(grade: out.b.grade?.json),
          ),
          for (final r in rows)
            _CompareRow(
              rowKey: r.key,
              label: r.label,
              better: r.better,
              a: _Value(r.a),
              b: _Value(r.b),
            ),
          PricePerScoopSection(
            servingA: out.a.servingSizeG,
            servingB: out.b.servingSizeG,
          ),
          const DisclaimerFooter(),
          for (final side in [out.a, out.b])
            if (side.attribution != null && side.barcode != null)
              OffAttribution(barcode: side.barcode!),
        ],
      ),
    );
  }
}

class _SideHeader extends StatelessWidget {
  const _SideHeader({required this.side});

  final CompareSide side;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final brand = side.brand;
    final status = memberStatusString(side.memberStatus);
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space3),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(side.name, style: theme.textTheme.titleMedium),
            if (brand != null)
              Text(
                brand,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            if (status != null) ...[
              const SizedBox(height: SnTokens.space2),
              VerdictBadge(status: status),
            ],
          ],
        ),
      ),
    );
  }
}

class _Value extends StatelessWidget {
  const _Value(this.value);

  final num? value;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final v = value;
    if (v == null) {
      return Text(
        l10n.resultNotOnLabel,
        style: theme.textTheme.bodySmall?.copyWith(
          color: c.textSecondary,
          fontStyle: FontStyle.italic,
        ),
      );
    }
    return Text(
      formatForDisplay(v),
      style: theme.textTheme.titleMedium?.copyWith(
        fontFeatures: const [FontFeature.tabularFigures()],
      ),
    );
  }
}

class _CompareRow extends StatelessWidget {
  const _CompareRow({
    required this.rowKey,
    required this.label,
    required this.better,
    required this.a,
    required this.b,
  });

  final String rowKey;
  final String label;
  final BetterSide better;
  final Widget a;
  final Widget b;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final note = switch (better) {
      BetterSide.a || BetterSide.b => null,
      BetterSide.same => l10n.compareBetterSame,
      _ => l10n.compareBetterUnknown,
    };
    Widget cell(String side, Widget value) => Row(
      children: [
        Flexible(child: value),
        if (better.json == side) ...[
          const SizedBox(width: SnTokens.space2),
          _BetterChip(
            key: Key('compare-better-$side-$rowKey'),
            semantics: side == 'a' ? l10n.compareBetterA : l10n.compareBetterB,
          ),
        ],
      ],
    );
    return Container(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space3),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: c.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(label, style: theme.textTheme.titleSmall),
          const SizedBox(height: SnTokens.space2),
          Row(
            children: [
              Expanded(child: cell('a', a)),
              const SizedBox(width: SnTokens.space2),
              Expanded(child: cell('b', b)),
            ],
          ),
          if (note != null)
            Padding(
              padding: const EdgeInsets.only(top: SnTokens.space1),
              child: Text(
                note,
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

/// "Better" on the side the API picked. A product comparison, not a member
/// verdict, so it uses the brand colour rather than a verdict colour.
class _BetterChip extends StatelessWidget {
  const _BetterChip({super.key, required this.semantics});

  final String semantics;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    return Semantics(
      label: semantics,
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: SnTokens.space2,
          vertical: SnTokens.space1 / 2,
        ),
        decoration: BoxDecoration(
          color: c.brandSoft,
          borderRadius: BorderRadius.circular(SnTokens.radiusFull),
          border: Border.all(color: c.brand),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.thumb_up_rounded,
              size: SnTokens.fontSizeMd,
              color: c.brand,
            ),
            const SizedBox(width: SnTokens.space1),
            Text(
              l10n.compareBetterChip,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: c.brandStrong,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
