import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/source_attribution.dart';
import '../../../shared/widgets/states.dart';
import '../data/foods_repository.dart';
import 'foods_providers.dart';

/// One search box over our foods, Indian dishes and packaged products.
/// Debounced; the groups come in the API's order (Indian foods first). A tap
/// calls [onPick].
class FoodSearchView extends ConsumerStatefulWidget {
  const FoodSearchView({super.key, required this.onPick, this.enabled = true});

  final void Function(FoodHit hit) onPick;
  final bool enabled;

  static const debounce = Duration(milliseconds: 300);
  static const fieldKey = Key('food-search-field');
  static const partialKey = Key('food-search-partial');
  static const emptyKey = Key('food-search-empty');
  static Key hitKey(FoodHit h) => Key('food-hit-${h.kind.json}-${h.id}');
  static Key groupKey(String name) => Key('food-group-$name');

  /// The API needs 2 to 80 characters.
  static const minLength = 2;

  @override
  ConsumerState<FoodSearchView> createState() => _FoodSearchViewState();
}

class _FoodSearchViewState extends ConsumerState<FoodSearchView> {
  final _controller = TextEditingController();
  Timer? _timer;
  String _query = '';

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _changed(String text) {
    _timer?.cancel();
    _timer = Timer(FoodSearchView.debounce, () {
      if (mounted) setState(() => _query = text.trim());
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          key: FoodSearchView.fieldKey,
          controller: _controller,
          maxLength: 80,
          textInputAction: TextInputAction.search,
          onChanged: _changed,
          decoration: InputDecoration(
            hintText: l10n.foodsSearchPlaceholder,
            prefixIcon: const Icon(Icons.search_rounded),
            counterText: '',
          ),
        ),
        const SizedBox(height: SnTokens.space2),
        if (_query.length >= FoodSearchView.minLength) _results(_query),
      ],
    );
  }

  Widget _results(String q) {
    final l10n = AppLocalizations.of(context);
    return ref
        .watch(foodSearchProvider(q))
        .when(
          loading: () => const LoadingSkeleton(lines: 3),
          error: (e, _) => ErrorState(
            message: localizedErrorCode(
              l10n,
              e is FoodsFailure ? e.code : apiErrorCode(e),
            ),
            onRetry: () => ref.invalidate(foodSearchProvider(q)),
          ),
          data: (out) {
            final c = SnColors.of(context);
            final theme = Theme.of(context);
            // Group order is the API's (indian, then packaged); a group with
            // no hits is not drawn.
            final indian = [
              for (final h in out.items)
                if (h.group == FoodHitGroup.indian) h,
            ];
            final packaged = [
              for (final h in out.items)
                if (h.group != FoodHitGroup.indian) h,
            ];
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (out.partial)
                  Padding(
                    padding: const EdgeInsets.only(bottom: SnTokens.space2),
                    child: InlineErrorBanner(
                      key: FoodSearchView.partialKey,
                      message: l10n.foodsPartialResults,
                    ),
                  ),
                if (out.items.isEmpty && !out.partial)
                  Padding(
                    key: FoodSearchView.emptyKey,
                    padding: const EdgeInsets.all(SnTokens.space3),
                    child: Text(
                      l10n.foodsNoResults,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                  ),
                if (indian.isNotEmpty)
                  _group('indian', l10n.foodsGroupIndian, indian),
                if (packaged.isNotEmpty)
                  _group('packaged', l10n.foodsGroupPackaged, packaged),
              ],
            );
          },
        );
  }

  Widget _group(String name, String title, List<FoodHit> hits) {
    final theme = Theme.of(context);
    return Column(
      key: FoodSearchView.groupKey(name),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: SnTokens.space2),
          child: Text(title, style: theme.textTheme.titleSmall),
        ),
        for (final h in hits) _tile(h),
      ],
    );
  }

  Widget _tile(FoodHit h) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final badge = h.isDish
        ? l10n.foodsKindDish
        : switch (h.kind) {
            FoodHitKind.food => l10n.foodsKindFood,
            _ => l10n.foodsKindProduct,
          };
    return ListTile(
      key: FoodSearchView.hitKey(h),
      contentPadding: EdgeInsets.zero,
      enabled: widget.enabled,
      title: Row(
        children: [
          Flexible(child: Text(h.name, style: theme.textTheme.titleSmall)),
          const SizedBox(width: SnTokens.space2),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: SnTokens.space2,
              vertical: SnTokens.space1 / 2,
            ),
            decoration: BoxDecoration(
              color: c.muted,
              borderRadius: BorderRadius.circular(SnTokens.radiusFull),
            ),
            child: Text(
              badge,
              style: theme.textTheme.labelSmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
          ),
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (h.brand != null && h.brand!.isNotEmpty)
            Text(h.brand!, style: theme.textTheme.bodySmall),
          SourceAttribution(
            keys: h.attributions,
            offBarcode: h.kind == FoodHitKind.off ? h.id : null,
          ),
        ],
      ),
      onTap: () => widget.onPick(h),
    );
  }
}
