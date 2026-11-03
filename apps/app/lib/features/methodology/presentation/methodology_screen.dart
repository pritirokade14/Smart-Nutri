import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';
import '../data/methodology_repository.dart';
import 'methodology_providers.dart';

/// `thresholds` of one section as (path, value) rows, in the API's order.
/// Nested maps join their keys with " › ", lists of values join with ", ",
/// and a list of maps shows each map as "key: value" pairs. Values are shown
/// exactly as sent (a whole double such as 5.0 shows as "5").
List<(String, String)> thresholdRows(Object? thresholds) {
  final rows = <(String, String)>[];
  void walk(String path, Object? value) {
    if (value == null) return;
    if (value is Map) {
      for (final e in value.entries) {
        walk(path.isEmpty ? '${e.key}' : '$path › ${e.key}', e.value);
      }
      return;
    }
    rows.add((path, _valueText(value)));
  }

  walk('', thresholds);
  return rows;
}

String _valueText(Object? value) => switch (value) {
  final double d when d == d.truncateToDouble() && d.isFinite =>
    d.toInt().toString(),
  final Map<Object?, Object?> m => [
    for (final e in m.entries)
      if (e.value != null) '${e.key}: ${_valueText(e.value)}',
  ].join(', '),
  final List<Object?> l =>
    l
        .where((v) => v != null)
        .map(_valueText)
        .join(l.any((v) => v is Map) ? ' · ' : ', '),
  _ => '$value',
};

/// The section title and description for a methodology section id, or null
/// for an id this build has no strings for (that section is not shown).
(String, String)? sectionText(AppLocalizations l10n, String id) => switch (id) {
  'nutriscore_2023' => (
    l10n.methodologySectionNutriscore2023Title,
    l10n.methodologySectionNutriscore2023Description,
  ),
  'high_in' => (
    l10n.methodologySectionHighInTitle,
    l10n.methodologySectionHighInDescription,
  ),
  'allergens' => (
    l10n.methodologySectionAllergensTitle,
    l10n.methodologySectionAllergensDescription,
  ),
  'diet' => (
    l10n.methodologySectionDietTitle,
    l10n.methodologySectionDietDescription,
  ),
  'claims' => (
    l10n.methodologySectionClaimsTitle,
    l10n.methodologySectionClaimsDescription,
  ),
  'blood_sugar' => (
    l10n.methodologySectionBloodSugarTitle,
    l10n.methodologySectionBloodSugarDescription,
  ),
  'hypertension' => (
    l10n.methodologySectionHypertensionTitle,
    l10n.methodologySectionHypertensionDescription,
  ),
  'weight_loss' => (
    l10n.methodologySectionWeightLossTitle,
    l10n.methodologySectionWeightLossDescription,
  ),
  'child' => (
    l10n.methodologySectionChildTitle,
    l10n.methodologySectionChildDescription,
  ),
  'infant' => (
    l10n.methodologySectionInfantTitle,
    l10n.methodologySectionInfantDescription,
  ),
  'custom_alerts' => (
    l10n.methodologySectionCustomAlertsTitle,
    l10n.methodologySectionCustomAlertsDescription,
  ),
  'daily_limits' => (
    l10n.methodologySectionDailyLimitsTitle,
    l10n.methodologySectionDailyLimitsDescription,
  ),
  _ => null,
};

/// "How we score" (F12): every rule with its live values and sources, as
/// `GET /v1/methodology` returns them. Values awaiting a clinician's review
/// say so; source links nobody has checked are labelled as such.
class MethodologyScreen extends ConsumerWidget {
  const MethodologyScreen({super.key});

  static Key sectionKey(String id) => Key('methodology-section-$id');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final result = ref.watch(methodologyProvider(l10n.localeName));
    return Scaffold(
      appBar: AppBar(title: Text(l10n.methodologyTitle)),
      body: result.when(
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
                e is MethodologyFailure ? e.code : null,
              ),
              icon: Icons.cloud_off_rounded,
              onRetry: () =>
                  ref.invalidate(methodologyProvider(l10n.localeName)),
            ),
          ),
        ),
        data: (m) => _MethodologyView(methodology: m),
      ),
    );
  }
}

class _MethodologyView extends ConsumerWidget {
  const _MethodologyView({required this.methodology});

  final Methodology methodology;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final m = methodology;
    final titles = {for (final s in m.sources) s.id: s.title};
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        SnTokens.space4,
        SnTokens.space2,
        SnTokens.space4,
        SnTokens.space6,
      ),
      children: [
        if (m.pendingClinicianReview)
          Container(
            margin: const EdgeInsets.only(bottom: SnTokens.space4),
            padding: const EdgeInsets.all(SnTokens.space3),
            decoration: BoxDecoration(
              color: c.muted,
              borderRadius: BorderRadius.circular(SnTokens.radiusMd),
              border: Border.all(color: c.borderStrong),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.pending_actions_rounded, color: c.textSecondary),
                const SizedBox(width: SnTokens.space2),
                Expanded(
                  child: Text(
                    l10n.methodologyPendingReview,
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
              ],
            ),
          ),
        Text(l10n.methodologyIntro, style: theme.textTheme.bodyLarge),
        const SizedBox(height: SnTokens.space4),
        for (final section in m.sections)
          if (sectionText(l10n, section.id) case (final title, final body))
            _SectionCard(
              key: MethodologyScreen.sectionKey(section.id),
              title: title,
              body: body,
              rows: thresholdRows(section.thresholds),
              sources: [
                for (final id in {
                  ...?section.thresholdSources,
                  ...?section.rationaleSources,
                })
                  ?titles[id],
              ],
            ),
        const SizedBox(height: SnTokens.space4),
        SectionHeader(
          title: l10n.methodologySourcesTitle,
          icon: Icons.menu_book_rounded,
        ),
        for (final source in m.sources) _SourceTile(source: source),
        const SizedBox(height: SnTokens.space3),
        Text(
          l10n.methodologyVersion(m.version),
          style: theme.textTheme.bodySmall?.copyWith(color: c.textSecondary),
        ),
        const DisclaimerFooter(),
      ],
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    super.key,
    required this.title,
    required this.body,
    required this.rows,
    required this.sources,
  });

  final String title;
  final String body;
  final List<(String, String)> rows;
  final List<String> sources;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.titleMedium),
            const SizedBox(height: SnTokens.space2),
            Text(body, style: theme.textTheme.bodyMedium),
            if (sources.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space2),
              Text(
                l10n.methodologySectionSources(sources.join('; ')),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.textSecondary,
                ),
              ),
            ],
            if (rows.isNotEmpty)
              Theme(
                data: theme.copyWith(dividerColor: c.border),
                child: ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(
                    bottom: SnTokens.space2,
                  ),
                  title: Text(
                    l10n.methodologyValuesTitle,
                    style: theme.textTheme.labelLarge,
                  ),
                  children: [
                    for (final (path, value) in rows)
                      Padding(
                        padding: const EdgeInsets.symmetric(
                          vertical: SnTokens.space1,
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              flex: 2,
                              child: Text(
                                path,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: c.textSecondary,
                                ),
                              ),
                            ),
                            const SizedBox(width: SnTokens.space2),
                            Expanded(
                              flex: 3,
                              child: Text(
                                value,
                                style: theme.textTheme.bodySmall,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// A cited document. Its link is shown as text with "Link not yet checked"
/// until a person has verified it, so it is never presented as authoritative.
class _SourceTile extends ConsumerWidget {
  const _SourceTile({required this.source});

  final MethodologySource source;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final url = source.url;
    final uri = url == null ? null : Uri.tryParse(url);
    return Padding(
      padding: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(source.title, style: theme.textTheme.bodyMedium),
          if (url != null && uri != null && uri.hasScheme)
            InkWell(
              onTap: () => ref.read(openExternalUrlProvider)(uri),
              child: Text(
                url,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: c.brandStrong,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          if (url != null && !source.urlVerified)
            Text(
              l10n.methodologyUrlUnverified,
              style: theme.textTheme.labelSmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
        ],
      ),
    );
  }
}
