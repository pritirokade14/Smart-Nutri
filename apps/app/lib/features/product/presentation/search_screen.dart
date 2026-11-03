import 'dart:async';

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
import '../../../shared/widgets/nutri_score_chip.dart';
import '../../../shared/widgets/off_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../data/product_discovery_repository.dart';
import 'discovery_routes.dart';
import 'product_discovery_providers.dart';

/// Product search (our catalogue and Open Food Facts). A hit opens its
/// result; with [compareWith] set, it becomes the second product of a
/// compare instead.
class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key, this.compareWith, this.memberId});

  final ProductRef? compareWith;
  final String? memberId;

  static const debounce = Duration(milliseconds: 400);

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _controller = TextEditingController();
  Timer? _timer;
  String _query = '';

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String text) {
    _timer?.cancel();
    _timer = Timer(SearchScreen.debounce, () => _submit(text));
  }

  void _submit(String text) {
    _timer?.cancel();
    final q = text.trim();
    if (q == _query) return;
    setState(() => _query = q);
    if (q.length >= searchMinLength) {
      // Event name only: never the query.
      ref.read(analyticsProvider).track('product_search');
    }
  }

  void _open(SearchHit hit) {
    final ref = (productId: hit.productId, barcode: hit.barcode);
    final a = widget.compareWith;
    if (a != null) {
      context.pushReplacement(
        compareLocation(a, ref, memberId: widget.memberId),
      );
    } else {
      context.push(resultLocation(ref));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final q = _query;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.compareWith == null ? l10n.searchTitle : l10n.compareTitle,
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(SnTokens.space4),
        children: [
          if (widget.compareWith != null)
            Padding(
              padding: const EdgeInsets.only(bottom: SnTokens.space3),
              child: Text(
                l10n.comparePickSecond,
                style: theme.textTheme.titleMedium,
              ),
            ),
          TextField(
            controller: _controller,
            autofocus: true,
            maxLength: searchMaxLength,
            textInputAction: TextInputAction.search,
            onChanged: _onChanged,
            onSubmitted: _submit,
            decoration: InputDecoration(
              hintText: l10n.searchPlaceholder,
              prefixIcon: const Icon(Icons.search_rounded),
              counterText: '',
            ),
          ),
          const SizedBox(height: SnTokens.space3),
          if (q.isEmpty)
            const SizedBox.shrink()
          else if (q.length < searchMinLength)
            Text(
              l10n.searchTooShort,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
            )
          else
            ref
                .watch(productSearchProvider(q))
                .when(
                  skipLoadingOnRefresh: false,
                  loading: () => const LoadingSkeleton(lines: 4),
                  error: (e, _) => ErrorState(
                    message: localizedErrorCode(
                      l10n,
                      e is DiscoveryFailure ? e.code : null,
                    ),
                    icon: Icons.cloud_off_rounded,
                    onRetry: () => ref.invalidate(productSearchProvider(q)),
                  ),
                  data: (hits) => hits.isEmpty
                      ? EmptyState(
                          icon: Icons.search_off_rounded,
                          title: l10n.searchNoResults,
                        )
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            for (final h in hits)
                              _HitTile(hit: h, onTap: () => _open(h)),
                            Text(
                              l10n.nutriscoreCalculatedBy,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: c.textSecondary,
                              ),
                            ),
                          ],
                        ),
                ),
        ],
      ),
    );
  }
}

class _HitTile extends StatelessWidget {
  const _HitTile({required this.hit, required this.onTap});

  final SearchHit hit;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final brand = hit.brand;
    final barcode = hit.barcode;
    final source = switch (hit.source) {
      SearchHitSource.ours => l10n.searchSourceOurs,
      SearchHitSource.off => l10n.searchSourceOff,
      _ => null,
    };
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space2),
      child: InkWell(
        borderRadius: BorderRadius.circular(SnTokens.radiusLg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(SnTokens.space3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  NutriScoreBadge(grade: hit.grade?.json),
                  const SizedBox(width: SnTokens.space3),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(hit.name, style: theme.textTheme.titleMedium),
                        if (brand != null)
                          Text(
                            brand,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: c.textSecondary,
                            ),
                          ),
                      ],
                    ),
                  ),
                  if (source != null)
                    Text(
                      source,
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                ],
              ),
              if (hit.attribution != null && barcode != null)
                OffAttribution(barcode: barcode),
            ],
          ),
        ),
      ),
    );
  }
}
