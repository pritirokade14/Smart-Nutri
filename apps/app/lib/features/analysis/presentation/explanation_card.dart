import 'package:flutter/material.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/reason_list.dart';
import '../domain/explanation_text.dart';

/// The AI explanation (F7), below the verdicts. It explains them and never
/// changes them; it is labelled as written by AI. Hidden when the API sent
/// none (`source == "unavailable"`: no ai_processing consent, or the model
/// failed or disagreed) or when a `member_N` token can't be resolved.
class ExplanationCard extends StatelessWidget {
  const ExplanationCard({
    super.key,
    required this.explanation,
    required this.verdicts,
  });

  final ExplanationOut explanation;

  /// The verdicts of the same response, for the members' names.
  final List<VerdictOut> verdicts;

  /// The explanation text and tips with names in place, or null when it must
  /// not be shown.
  static ({String text, List<String> tips})? resolve(
    AppLocalizations l10n,
    ExplanationOut e,
    List<VerdictOut> verdicts,
  ) {
    if (e.source != ExplanationOutSource.llm) return null;
    final raw = e.text;
    if (raw == null || raw.trim().isEmpty) return null;
    final names = {
      for (final v in verdicts)
        v.memberId: v.memberName.isEmpty ? l10n.resultYou : v.memberName,
    };
    final text = substituteMemberTokens(raw, e.memberRefs, names);
    if (text == null) return null;
    final tips = <String>[];
    for (final tip in e.tips) {
      final t = substituteMemberTokens(tip, e.memberRefs, names);
      if (t == null) return null;
      tips.add(t);
    }
    return (text: text, tips: tips);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final resolved = resolve(l10n, explanation, verdicts);
    if (resolved == null) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(vertical: SnTokens.space2),
      child: Padding(
        padding: const EdgeInsets.all(SnTokens.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.auto_awesome_rounded, color: c.brand),
                const SizedBox(width: SnTokens.space2),
                Expanded(
                  child: Semantics(
                    header: true,
                    child: Text(
                      l10n.explanationTitle,
                      style: theme.textTheme.titleMedium,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: SnTokens.space1),
            Text(
              l10n.explanationAiNote,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
            const SizedBox(height: SnTokens.space3),
            Text(resolved.text, style: theme.textTheme.bodyMedium),
            if (resolved.tips.isNotEmpty) ...[
              const SizedBox(height: SnTokens.space3),
              Text(
                l10n.explanationTipsTitle,
                style: theme.textTheme.titleSmall,
              ),
              const SizedBox(height: SnTokens.space1),
              for (final tip in resolved.tips) ReasonBullet(text: tip),
            ],
          ],
        ),
      ),
    );
  }
}
