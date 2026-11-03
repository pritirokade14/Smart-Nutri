import 'package:flutter/material.dart';

import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';

/// One reason line with a neutral bullet. The bullet never carries a verdict
/// colour: a reason's meaning is in its text.
class ReasonBullet extends StatelessWidget {
  const ReasonBullet({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final c = SnColors.of(context);
    final style = Theme.of(context).textTheme.bodyMedium;
    final lineHeight =
        (style?.fontSize ?? SnTokens.fontSizeMd) * (style?.height ?? 1.4);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: SnTokens.space1),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: lineHeight,
            child: Center(
              child: Container(
                width: SnTokens.space2 - SnTokens.space1 / 2,
                height: SnTokens.space2 - SnTokens.space1 / 2,
                decoration: BoxDecoration(
                  color: c.textSecondary,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ),
          const SizedBox(width: SnTokens.space3),
          Expanded(child: Text(text, style: style)),
        ],
      ),
    );
  }
}

/// Reasons in the order given (the API's order; never re-sorted here).
class ReasonList extends StatelessWidget {
  const ReasonList({super.key, required this.reasons});

  final List<String> reasons;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [for (final r in reasons) ReasonBullet(text: r)],
  );
}
