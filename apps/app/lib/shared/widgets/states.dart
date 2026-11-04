import 'package:flutter/material.dart';

import '../../core/l10n/app_localizations.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';
import 'buttons.dart';

/// A friendly "nothing here yet" panel: an icon in a soft circle, a title,
/// an optional line of body text and an optional action.
class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.body,
    this.action,
  });

  final IconData icon;
  final String title;
  final String? body;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final body = this.body;
    final action = this.action;
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space5,
        vertical: SnTokens.space6,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: SnTokens.space8 + SnTokens.space4,
            height: SnTokens.space8 + SnTokens.space4,
            decoration: BoxDecoration(
              color: c.brandSoft,
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              size: SnTokens.space6 + SnTokens.space1,
              color: c.brand,
            ),
          ),
          const SizedBox(height: SnTokens.space4),
          Text(
            title,
            style: theme.textTheme.titleLarge,
            textAlign: TextAlign.center,
          ),
          if (body != null) ...[
            const SizedBox(height: SnTokens.space2),
            Text(
              body,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: c.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
          if (action != null) ...[
            const SizedBox(height: SnTokens.space4),
            action,
          ],
        ],
      ),
    );
  }
}

/// A compact error message inside a form, with an optional action.
class InlineErrorBanner extends StatelessWidget {
  const InlineErrorBanner({super.key, required this.message, this.action});

  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(SnTokens.space3),
      decoration: BoxDecoration(
        color: c.verdictAvoidSurface,
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
        border: Border.all(color: c.verdictAvoid),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline_rounded, color: c.verdictAvoid),
          const SizedBox(width: SnTokens.space2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: c.textPrimary,
                  ),
                ),
                ?action,
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// A "Coming soon" pill for tabs that later releases fill in.
class ComingSoonPill extends StatelessWidget {
  const ComingSoonPill({super.key});

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space3,
        vertical: SnTokens.space1,
      ),
      decoration: BoxDecoration(
        color: c.accentPeach,
        borderRadius: BorderRadius.circular(SnTokens.radiusFull),
      ),
      child: Text(
        AppLocalizations.of(context).commonComingSoon,
        style: Theme.of(
          context,
        ).textTheme.labelMedium?.copyWith(color: c.textPrimary),
      ),
    );
  }
}

/// A tab placeholder: the tab's title in the app bar and a centred
/// [EmptyState] marked "Coming soon", with optional [extra] actions below.
class ComingSoonScaffold extends StatelessWidget {
  const ComingSoonScaffold({
    super.key,
    required this.title,
    required this.icon,
    required this.headline,
    required this.body,
    this.extra = const [],
  });

  final String title;
  final IconData icon;
  final String headline;
  final String body;
  final List<Widget> extra;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            EmptyState(
              icon: icon,
              title: headline,
              body: body,
              action: const ComingSoonPill(),
            ),
            ...extra,
          ],
        ),
      ),
    ),
  );
}

/// A failure the user can act on: the message, a retry (when [onRetry] is
/// set) and any extra [actions].
class ErrorState extends StatelessWidget {
  const ErrorState({
    super.key,
    required this.message,
    this.title,
    this.onRetry,
    this.retryLabel,
    this.actions = const [],
    this.icon = Icons.error_outline_rounded,
  });

  final String message;
  final String? title;
  final VoidCallback? onRetry;

  /// Defaults to "Try again".
  final String? retryLabel;
  final List<Widget> actions;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final title = this.title;
    final onRetry = this.onRetry;
    return Padding(
      padding: const EdgeInsets.all(SnTokens.space5),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: SnTokens.space8,
              height: SnTokens.space8,
              decoration: BoxDecoration(color: c.muted, shape: BoxShape.circle),
              child: Icon(icon, size: SnTokens.space6, color: c.textSecondary),
            ),
          ),
          const SizedBox(height: SnTokens.space4),
          if (title != null) ...[
            Text(
              title,
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: SnTokens.space2),
          ],
          Text(
            message,
            style: title == null
                ? theme.textTheme.titleMedium
                : theme.textTheme.bodyMedium?.copyWith(color: c.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: SnTokens.space5),
          if (onRetry != null) ...[
            PrimaryButton(
              label: retryLabel ?? l10n.commonRetry,
              icon: Icons.refresh_rounded,
              onPressed: onRetry,
            ),
            const SizedBox(height: SnTokens.space2),
          ],
          for (final a in actions) ...[
            a,
            const SizedBox(height: SnTokens.space2),
          ],
        ],
      ),
    );
  }
}

/// A placeholder block while content loads. It pulses gently unless the
/// platform asks for reduced motion.
class SkeletonBox extends StatelessWidget {
  const SkeletonBox({
    super.key,
    this.width,
    this.height = SnTokens.space4,
    this.radius = SnTokens.radiusSm,
  });

  final double? width;
  final double height;
  final double radius;

  @override
  Widget build(BuildContext context) => Container(
    width: width,
    height: height,
    decoration: BoxDecoration(
      color: SnColors.of(context).muted,
      borderRadius: BorderRadius.circular(radius),
    ),
  );
}

/// Loading placeholder: a card-shaped block followed by [lines] text bars.
/// Announced to screen readers as "Loading…".
class LoadingSkeleton extends StatefulWidget {
  const LoadingSkeleton({super.key, this.lines = 3, this.card = false});

  final int lines;

  /// Add a tall card-shaped block before the lines.
  final bool card;

  @override
  State<LoadingSkeleton> createState() => _LoadingSkeletonState();
}

class _LoadingSkeletonState extends State<LoadingSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
    lowerBound: 0.45,
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final still = MediaQuery.maybeDisableAnimationsOf(context) ?? false;
    if (still) {
      _pulse
        ..stop()
        ..value = 1;
    } else if (!_pulse.isAnimating) {
      _pulse.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    // Bars of varied width read as text.
    const widths = [1.0, 0.8, 0.9, 0.6];
    return Semantics(
      label: l10n.commonLoading,
      liveRegion: true,
      excludeSemantics: true,
      child: FadeTransition(
        opacity: _pulse,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final full = constraints.maxWidth.isFinite
                ? constraints.maxWidth
                : SnTokens.space8 * 4;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (widget.card) ...[
                  SkeletonBox(
                    width: full,
                    height: SnTokens.space8 * 2,
                    radius: SnTokens.radiusLg,
                  ),
                  const SizedBox(height: SnTokens.space4),
                ],
                for (var i = 0; i < widget.lines; i++) ...[
                  SkeletonBox(width: full * widths[i % widths.length]),
                  if (i < widget.lines - 1)
                    const SizedBox(height: SnTokens.space3),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}
