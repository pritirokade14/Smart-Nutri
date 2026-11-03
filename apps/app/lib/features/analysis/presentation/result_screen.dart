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
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/nutri_score_chip.dart';
import '../../../shared/widgets/nutrient_row.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../../scan/domain/barcode.dart';
import '../../scan/domain/number_text.dart';
import '../data/analysis_repository.dart';
import '../domain/report.dart';
import 'analysis_providers.dart';
import 'claims_section.dart';
import 'verdict_card.dart';

/// Result of a barcode scan or of a product saved from a label: the product,
/// its Nutri-Score (calculated by SmartNutri), "high in" flags and one verdict
/// card per member, all exactly as the API returned them.
class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key, this.barcode, this.productId});

  final String? barcode;

  /// Set for a product saved from the confirm screen (`/result?product_id=`).
  final String? productId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final productId = this.productId;
    final AnalyzeQuery query;
    String? code;
    if (productId != null && productId.isNotEmpty) {
      query = (barcode: null, productId: productId, language: l10n.localeName);
    } else {
      // S8: same normalisation as the API; an invalid deep-link barcode never
      // reaches it.
      code = normalizeBarcode(barcode ?? '');
      if (code == null) {
        return Scaffold(
          appBar: AppBar(title: Text(l10n.resultTitle)),
          body: _ErrorView(message: l10n.errorInvalidBarcode),
        );
      }
      query = (barcode: code, productId: null, language: l10n.localeName);
    }
    final result = ref.watch(analyzeResultProvider(query));
    return Scaffold(
      appBar: AppBar(title: Text(l10n.resultTitle)),
      body: result.when(
        skipLoadingOnRefresh: false,
        loading: () => const SingleChildScrollView(
          padding: EdgeInsets.all(SnTokens.space4),
          child: LoadingSkeleton(card: true, lines: 4),
        ),
        error: (error, _) => _ErrorView(
          message: _errorMessage(l10n, error),
          // An invalid barcode cannot succeed on retry.
          onRetry: error is AnalysisInvalidBarcode
              ? null
              : () => ref.invalidate(analyzeResultProvider(query)),
          // F15: an unknown barcode leads to the label photo flow, carrying
          // the barcode through to the scan and the saved product.
          labelBarcode: error is AnalysisNotFound ? code : null,
        ),
        data: (out) => _ResultView(out: out, barcode: code),
      ),
    );
  }

  static String _errorMessage(AppLocalizations l10n, Object error) =>
      switch (error) {
        AnalysisNotFound() => l10n.scanNotFound,
        AnalysisUnavailable() => l10n.scanOffUnavailable,
        AnalysisInvalidBarcode() => l10n.errorInvalidBarcode,
        AnalysisNetworkFailure() => l10n.errorNetwork,
        AnalysisApiFailure(:final cause) => localizedApiError(l10n, cause),
        _ => l10n.errorInternalError,
      };
}

class _ErrorView extends StatefulWidget {
  const _ErrorView({required this.message, this.onRetry, this.labelBarcode});

  final String message;
  final VoidCallback? onRetry;

  /// When set, this unknown barcode goes straight to label capture (F15, as
  /// on the web); the button stays as a fallback.
  final String? labelBarcode;

  @override
  State<_ErrorView> createState() => _ErrorViewState();
}

class _ErrorViewState extends State<_ErrorView> {
  @override
  void initState() {
    super.initState();
    final code = widget.labelBarcode;
    if (code == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      GoRouter.maybeOf(context)?.pushReplacement('/scan/label?barcode=$code');
    });
  }

  @override
  Widget build(BuildContext context) {
    final onRetry = widget.onRetry;
    final labelBarcode = widget.labelBarcode;
    final l10n = AppLocalizations.of(context);
    return Center(
      child: SingleChildScrollView(
        child: ErrorState(
          message: widget.message,
          icon: labelBarcode == null
              ? Icons.cloud_off_rounded
              : Icons.search_off_rounded,
          actions: [
            if (labelBarcode case final code?)
              PrimaryButton(
                label: l10n.notfoundGoToLabel,
                icon: Icons.photo_camera_outlined,
                onPressed: () =>
                    context.pushReplacement('/scan/label?barcode=$code'),
              ),
            if (onRetry != null)
              labelBarcode == null
                  ? PrimaryButton(
                      label: l10n.scanRetry,
                      icon: Icons.refresh_rounded,
                      onPressed: onRetry,
                    )
                  : SecondaryButton(
                      label: l10n.scanRetry,
                      icon: Icons.refresh_rounded,
                      onPressed: onRetry,
                    ),
            TextButton(
              onPressed: () => context.pushReplacement('/scan'),
              child: Text(l10n.resultScanAnother),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({required this.out, required this.barcode});

  final AnalyzeOut out;
  final String? barcode;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final product = out.product;
    final highIn = [
      for (final code in highInCodes(out.report)) ?_highInLabel(l10n, code),
    ];
    final claims = claimChecks(out.report);
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space4,
        SnTokens.space2,
        SnTokens.space4,
        SnTokens.space6,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _ProductCard(
            name: product.name ?? product.barcode ?? barcode ?? '',
            brand: product.brand,
            grade: nutriscoreGrade(out.report),
            highIn: highIn,
          ),
          const SizedBox(height: SnTokens.space5),
          SectionHeader(
            title: l10n.resultFamilyTitle,
            icon: Icons.groups_rounded,
          ),
          // One card per member, in the order the API returned them.
          for (final v in out.verdicts) VerdictCard(verdict: v),
          const DisclaimerFooter(),
          const SizedBox(height: SnTokens.space3),
          SectionHeader(
            title: l10n.resultNutritionTitle,
            icon: Icons.table_rows_rounded,
          ),
          _NutritionTable(per100g: product.per100g),
          if (claims.isNotEmpty) ...[
            const SizedBox(height: SnTokens.space5),
            ClaimsSection(checks: claims),
          ],
          if (product.attribution != null)
            if (product.barcode ?? barcode case final code?) ...[
              const SizedBox(height: SnTokens.space2),
              OffAttribution(barcode: code),
            ],
          const SizedBox(height: SnTokens.space4),
          SecondaryButton(
            label: l10n.resultScanAnother,
            icon: Icons.qr_code_scanner_rounded,
            onPressed: () => context.pushReplacement('/scan'),
          ),
        ],
      ),
    );
  }

  static String? _highInLabel(AppLocalizations l10n, String code) =>
      switch (code) {
        'sugar' => l10n.highInSugar,
        'fat' => l10n.highInFat,
        'sat_fat' => l10n.highInSatFat,
        'salt' => l10n.highInSalt,
        _ => null,
      };
}

/// The product, its Nutri-Score and its "high in" flags, as the API sent
/// them.
class _ProductCard extends StatelessWidget {
  const _ProductCard({
    required this.name,
    required this.brand,
    required this.grade,
    required this.highIn,
  });

  final String name;
  final String? brand;
  final String? grade;
  final List<String> highIn;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final brand = this.brand;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: SnTokens.space7,
                  height: SnTokens.space7,
                  decoration: BoxDecoration(
                    color: c.accentPeach,
                    borderRadius: BorderRadius.circular(SnTokens.radiusMd),
                  ),
                  child: Icon(Icons.inventory_2_outlined, color: c.brandStrong),
                ),
                const SizedBox(width: SnTokens.space3),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(name, style: theme.textTheme.headlineSmall),
                      if (brand != null)
                        Text(
                          brand,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: c.textSecondary,
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: SnTokens.space4),
            NutriScoreChip(grade: grade),
            if (highIn.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space4),
              Text(l10n.resultHighInTitle, style: theme.textTheme.titleSmall),
              const SizedBox(height: SnTokens.space2),
              Wrap(
                spacing: SnTokens.space2,
                runSpacing: SnTokens.space2,
                children: [for (final label in highIn) _HighInChip(label)],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// A product-level "high in" flag (not a member verdict): amber tint and an
/// arrow, so it never relies on colour alone.
class _HighInChip extends StatelessWidget {
  const _HighInChip(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space3,
        vertical: SnTokens.space1,
      ),
      decoration: BoxDecoration(
        color: c.verdictCautionSurface,
        borderRadius: BorderRadius.circular(SnTokens.radiusFull),
        border: Border.all(color: c.verdictCaution),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.arrow_upward_rounded,
            size: SnTokens.fontSizeMd,
            color: c.verdictCaution,
          ),
          const SizedBox(width: SnTokens.space1),
          Text(
            label,
            style: Theme.of(
              context,
            ).textTheme.labelMedium?.copyWith(color: c.textPrimary),
          ),
        ],
      ),
    );
  }
}

/// `product.per_100g` as the API sent it; a missing value says so and is
/// never shown as 0.
class _NutritionTable extends StatelessWidget {
  const _NutritionTable({required this.per100g});

  final NutrientsOut per100g;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final n = per100g;
    final rows = <(String, num?)>[
      (l10n.confirmFieldEnergyKcal, n.energyKcal),
      (l10n.confirmFieldProteinG, n.proteinG),
      (l10n.confirmFieldCarbsG, n.carbsG),
      (l10n.confirmFieldSugarsG, n.sugarsG),
      (l10n.confirmFieldFatG, n.fatG),
      (l10n.confirmFieldSatFatG, n.satFatG),
      (l10n.confirmFieldFiberG, n.fiberG),
      (l10n.confirmFieldSaltG, n.saltG),
      (l10n.confirmFieldSodiumMg, n.sodiumMg),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: SnTokens.space4,
          vertical: SnTokens.space2,
        ),
        child: Column(
          children: [
            for (final (i, (label, value)) in rows.indexed)
              NutrientRow(
                label: label,
                value: value == null ? null : formatForDisplay(value),
                divider: i < rows.length - 1,
              ),
          ],
        ),
      ),
    );
  }
}
