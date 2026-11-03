import 'package:flutter/material.dart';

import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// A section title with an optional icon, subtitle and trailing action.
class SectionHeader extends StatelessWidget {
  const SectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.icon,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final IconData? icon;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final icon = this.icon;
    final subtitle = this.subtitle;
    return Padding(
      padding: const EdgeInsets.only(bottom: SnTokens.space3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (icon != null) ...[
            Container(
              padding: const EdgeInsets.all(SnTokens.space2),
              decoration: BoxDecoration(
                color: c.brandSoft,
                borderRadius: BorderRadius.circular(SnTokens.radiusMd),
              ),
              child: Icon(
                icon,
                size: SnTokens.fontSizeLg,
                color: c.brandStrong,
              ),
            ),
            const SizedBox(width: SnTokens.space3),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Semantics(
                  header: true,
                  child: Text(title, style: theme.textTheme.titleLarge),
                ),
                if (subtitle != null)
                  Text(
                    subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: c.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
          ?trailing,
        ],
      ),
    );
  }
}
