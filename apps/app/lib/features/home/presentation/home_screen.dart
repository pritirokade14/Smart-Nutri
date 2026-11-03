import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/states.dart';

final meProvider = FutureProvider.autoDispose<MeOut>(
  (ref) => ref.watch(apiClientProvider).me.meGet(),
  // Show API errors immediately; the user retries with the button.
  retry: (_, _) => null,
);

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final me = ref.watch(meProvider);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(
            SnTokens.space4,
            SnTokens.space4,
            SnTokens.space4,
            SnTokens.space5,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _Wordmark(),
              const SizedBox(height: SnTokens.space5),
              me.when(
                loading: () => const LoadingSkeleton(lines: 2),
                error: (e, _) => Card(
                  child: ErrorState(
                    message: localizedApiError(l10n, e),
                    icon: Icons.cloud_off_rounded,
                    onRetry: () => ref.invalidate(meProvider),
                  ),
                ),
                data: (m) {
                  final name = m.displayName ?? m.email ?? '';
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name.isEmpty
                            ? l10n.homeWelcomeNoName
                            : l10n.homeWelcome(name),
                        style: theme.textTheme.headlineMedium,
                      ),
                      const SizedBox(height: SnTokens.space1),
                      Text(
                        l10n.homeSubtitle,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: c.textSecondary,
                        ),
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: SnTokens.space5),
              _ActionCard(
                icon: Icons.qr_code_scanner_rounded,
                title: l10n.homeScanCta,
                body: l10n.homeScanBody,
                emphasis: true,
                onTap: () => context.push('/scan'),
              ),
              const SizedBox(height: SnTokens.space3),
              _ActionCard(
                icon: Icons.photo_camera_outlined,
                title: l10n.homeLabelTitle,
                body: l10n.homeLabelBody,
                onTap: () => context.push('/scan/label'),
              ),
              const SizedBox(height: SnTokens.space6),
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
              const SizedBox(height: SnTokens.space3),
              const DisclaimerFooter(),
            ],
          ),
        ),
      ),
    );
  }
}

/// The app name with a small brand mark.
class _Wordmark extends StatelessWidget {
  const _Wordmark();

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Row(
      children: [
        Container(
          width: SnTokens.space6,
          height: SnTokens.space6,
          decoration: BoxDecoration(color: c.brand, shape: BoxShape.circle),
          child: Icon(
            Icons.eco_rounded,
            size: SnTokens.fontSizeLg,
            color: c.textInverse,
          ),
        ),
        const SizedBox(width: SnTokens.space2),
        Text(
          AppLocalizations.of(context).appName,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(color: c.brandStrong),
        ),
      ],
    );
  }
}

/// A big tappable card for one of the two ways to check a product.
class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.icon,
    required this.title,
    required this.body,
    required this.onTap,
    this.emphasis = false,
  });

  final IconData icon;
  final String title;
  final String body;
  final VoidCallback onTap;

  /// The main action, filled with the brand colour.
  final bool emphasis;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final background = emphasis ? c.brand : c.surface;
    final foreground = emphasis ? c.textInverse : c.textPrimary;
    final secondary = emphasis ? c.textInverse : c.textSecondary;
    return Semantics(
      button: true,
      child: Material(
        color: background,
        borderRadius: BorderRadius.circular(SnTokens.radiusXl),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.all(SnTokens.space5),
            decoration: emphasis
                ? null
                : BoxDecoration(
                    borderRadius: BorderRadius.circular(SnTokens.radiusXl),
                    border: Border.all(color: c.border),
                  ),
            child: Row(
              children: [
                Container(
                  width: SnTokens.space7 + SnTokens.space2,
                  height: SnTokens.space7 + SnTokens.space2,
                  decoration: BoxDecoration(
                    color: emphasis ? c.brandStrong : c.accentPeach,
                    borderRadius: BorderRadius.circular(SnTokens.radiusLg),
                  ),
                  child: Icon(
                    icon,
                    size: SnTokens.fontSize2xl,
                    color: emphasis ? c.textInverse : c.brandStrong,
                  ),
                ),
                const SizedBox(width: SnTokens.space4),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: theme.textTheme.titleLarge?.copyWith(
                          color: foreground,
                        ),
                      ),
                      const SizedBox(height: SnTokens.space1),
                      Text(
                        body,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: secondary,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: SnTokens.space2),
                Icon(Icons.chevron_right_rounded, color: secondary),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
