import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../data/meals_repository.dart';
import 'log_meal_sheet.dart';
import 'meals_providers.dart';

/// "I ate this" on a member's verdict card: opens the log sheet for that
/// member, then confirms with an Undo (or says it was saved offline).
class IAteThisButton extends ConsumerWidget {
  const IAteThisButton({
    super.key,
    required this.product,
    required this.verdicts,
    required this.memberId,
  });

  final LogMealProduct product;
  final List<VerdictOut> verdicts;
  final String memberId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: OutlinedButton.icon(
        key: Key('i-ate-this-$memberId'),
        icon: const Icon(Icons.restaurant_rounded),
        label: Text(l10n.mealsLogCta),
        onPressed: () => _open(context, ref),
      ),
    );
  }

  Future<void> _open(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final result = await showLogMealSheet(
      context,
      product: product,
      verdicts: verdicts,
      memberId: memberId,
    );
    switch (result) {
      case null:
        return;
      case MealQueued():
        messenger.showSnackBar(
          SnackBar(content: Text(l10n.mealsQueuedOffline)),
        );
      case MealLogged(:final meal):
        final who = [
          for (final v in verdicts)
            if (v.memberId == meal.memberId) memberLabel(l10n, v),
        ].firstOrNull;
        final repo = ref.read(mealsRepositoryProvider);
        final revision = ref.read(mealsRevisionProvider.notifier);
        messenger.showSnackBar(
          SnackBar(
            content: Text(l10n.mealsLogSaved(who ?? l10n.resultYou)),
            action: SnackBarAction(
              label: l10n.mealsLogUndo,
              onPressed: () async {
                try {
                  await repo.delete(meal.id);
                  revision.bump();
                  messenger.showSnackBar(
                    SnackBar(content: Text(l10n.mealsLogUndone)),
                  );
                } on MealsFailure catch (e) {
                  messenger.showSnackBar(
                    SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
                  );
                }
              },
            ),
          ),
        );
    }
  }
}
