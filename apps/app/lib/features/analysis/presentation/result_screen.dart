import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../data/analysis_repository.dart';
import '../domain/report.dart';
import 'analysis_providers.dart';
import 'verdict_card.dart';

/// Result of a barcode scan: the product, its Nutri-Score (calculated by
/// SmartNutri), "high in" flags and one verdict card per member, all exactly
/// as the API returned them.
class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key, required this.barcode});

  final String barcode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final query = (barcode: barcode, language: l10n.localeName);
    final result = ref.watch(analyzeResultProvider(query));
    return Scaffold(
      appBar: AppBar(title: Text(l10n.resultTitle)),
      body: result.when(
        skipLoadingOnRefresh: false,
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _ErrorView(
          message: _errorMessage(l10n, error),
          onRetry: () => ref.invalidate(analyzeResultProvider(query)),
        ),
        data: (out) => _ResultView(out: out, barcode: barcode),
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

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space5),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: SnTokens.space4),
            FilledButton(onPressed: onRetry, child: Text(l10n.scanRetry)),
            const SizedBox(height: SnTokens.space2),
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
  final String barcode;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final product = out.product;
    final highIn = [
      for (final code in highInCodes(out.report)) ?_highInLabel(l10n, code),
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.all(SnTokens.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            product.name ?? product.barcode ?? barcode,
            style: theme.textTheme.headlineSmall,
          ),
          if (product.brand case final brand?)
            Text(brand, style: theme.textTheme.bodyMedium),
          const SizedBox(height: SnTokens.space3),
          _GradeChip(grade: nutriscoreGrade(out.report)),
          if (highIn.isNotEmpty) ...[
            const SizedBox(height: SnTokens.space3),
            Text(l10n.resultHighInTitle, style: theme.textTheme.titleSmall),
            const SizedBox(height: SnTokens.space1),
            Wrap(
              spacing: SnTokens.space2,
              runSpacing: SnTokens.space1,
              children: [for (final label in highIn) Chip(label: Text(label))],
            ),
          ],
          const SizedBox(height: SnTokens.space3),
          // One card per member, in the order the API returned them.
          for (final v in out.verdicts) VerdictCard(verdict: v),
          const SizedBox(height: SnTokens.space3),
          Text(l10n.commonDisclaimer, style: theme.textTheme.bodySmall),
          if (product.attribution != null)
            OffAttribution(barcode: product.barcode ?? barcode),
          const SizedBox(height: SnTokens.space3),
          OutlinedButton(
            onPressed: () => context.pushReplacement('/scan'),
            child: Text(l10n.resultScanAnother),
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

class _GradeChip extends StatelessWidget {
  const _GradeChip({required this.grade});

  final String? grade;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final grade = this.grade;
    if (grade == null) {
      return Text(
        l10n.nutriscoreInsufficientData,
        style: theme.textTheme.bodyMedium,
      );
    }
    final (background, foreground) = switch (grade) {
      'A' => (SnTokens.gradeA, SnTokens.surfaceDefault),
      'B' => (SnTokens.gradeB, SnTokens.textPrimary),
      'C' => (SnTokens.gradeC, SnTokens.textPrimary),
      'D' => (SnTokens.gradeD, SnTokens.textPrimary),
      _ => (SnTokens.gradeE, SnTokens.surfaceDefault),
    };
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(
            horizontal: SnTokens.space3,
            vertical: SnTokens.space1,
          ),
          decoration: BoxDecoration(
            color: background,
            borderRadius: BorderRadius.circular(SnTokens.radiusLg),
          ),
          child: Text(
            l10n.resultGrade(grade),
            style: theme.textTheme.labelLarge?.copyWith(color: foreground),
          ),
        ),
        const SizedBox(width: SnTokens.space2),
        Expanded(
          child: Text(
            l10n.nutriscoreCalculatedBy,
            style: theme.textTheme.bodySmall,
          ),
        ),
      ],
    );
  }
}
