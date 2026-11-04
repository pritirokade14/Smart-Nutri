import 'package:flutter/material.dart';

import '../../../../core/theme/sn_colors.dart';
import '../../../../core/theme/tokens.g.dart';

/// The common look of a Home card: an icon, a title and the body.
class HomeCardFrame extends StatelessWidget {
  const HomeCardFrame({
    super.key,
    required this.title,
    required this.icon,
    required this.child,
    this.action,
  });

  final String title;
  final IconData icon;
  final Widget child;

  /// An optional call to action under the body.
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(icon, color: c.brandStrong),
                const SizedBox(width: SnTokens.space2),
                Expanded(
                  child: Text(title, style: theme.textTheme.titleMedium),
                ),
              ],
            ),
            const SizedBox(height: SnTokens.space2),
            child,
            if (action case final a?) ...[
              const SizedBox(height: SnTokens.space2),
              Align(alignment: AlignmentDirectional.centerStart, child: a),
            ],
          ],
        ),
      ),
    );
  }
}

/// Secondary body text for a card.
class CardBody extends StatelessWidget {
  const CardBody(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) => Text(
    text,
    style: Theme.of(
      context,
    ).textTheme.bodyMedium?.copyWith(color: SnColors.of(context).textSecondary),
  );
}
