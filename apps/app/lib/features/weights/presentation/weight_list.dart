import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/meal_queue.dart';
import '../../../core/theme/sn_colors.dart';
import '../../diary/domain/diary_dates.dart';
import '../../targets/domain/targets_format.dart';
import '../data/weights_repository.dart';
import 'weigh_in_sheet.dart';
import 'weights_providers.dart';

String _dateText(AppLocalizations l10n, DateTime d) =>
    (DateFormat.yMMMd(l10n.localeName)..useNativeDigits = false).format(d);

/// The weigh-ins, newest first, with edit and delete. A weigh-in waiting on
/// the phone shows "Waiting to sync" (or "Check this weigh-in" when the API
/// asked for a confirmation). The kilograms show only when the API sent them
/// and [numbersHidden] is false.
class WeightList extends ConsumerWidget {
  const WeightList({
    super.key,
    required this.items,
    required this.pending,
    required this.numbersHidden,
  });

  final List<WeightOut> items;
  final List<PendingWeighIn> pending;

  /// True when the API hides the numbers; also the offline default, so a
  /// queued weigh-in never shows a number the user chose to hide.
  final bool numbersHidden;

  static Key tileKey(String date) => Key('weight-$date');
  static Key pendingKey(String clientId) => Key('weight-pending-$clientId');
  static Key editKey(String date) => Key('weight-edit-$date');
  static Key deleteKey(String date) => Key('weight-delete-$date');
  static Key confirmPendingKey(String clientId) =>
      Key('weight-pending-confirm-$clientId');
  static Key discardPendingKey(String clientId) =>
      Key('weight-pending-discard-$clientId');

  Future<void> _delete(BuildContext context, WidgetRef ref, String date) async {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(l10n.weightDeleteConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(material.cancelButtonLabel),
          ),
          TextButton(
            key: const Key('weight-delete-confirm'),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.weightDelete),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(weightsRepositoryProvider).delete(date);
      refreshWeights(ref);
    } on WeightsFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final c = SnColors.of(context);
    final small = Theme.of(
      context,
    ).textTheme.bodySmall?.copyWith(color: c.textSecondary);
    return Column(
      children: [
        for (final r in pending)
          ListTile(
            key: pendingKey(r.clientId),
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.cloud_upload_outlined, color: c.textSecondary),
            title: Text(
              numbersHidden
                  ? _dateText(l10n, parseDateKey(r.localDate)!)
                  : '${_dateText(l10n, parseDateKey(r.localDate)!)} · '
                        '${l10n.weightKgValue(formatDecimal(r.weightKg))}',
            ),
            subtitle: Text(
              r.status == WeighInStatus.needsConfirm
                  ? l10n.weightCheckEntry
                  : l10n.diaryWaitingSync,
              style: small,
            ),
            trailing: r.status == WeighInStatus.needsConfirm
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextButton(
                        key: confirmPendingKey(r.clientId),
                        onPressed: () async {
                          final queue = ref.read(weighInQueueProvider);
                          await queue.confirmWeighIn(r.clientId);
                          await ref.read(weighInSyncProvider).flush();
                          refreshWeights(ref);
                        },
                        child: Text(l10n.weightSaveAnyway),
                      ),
                      IconButton(
                        key: discardPendingKey(r.clientId),
                        tooltip: l10n.weightDelete,
                        icon: const Icon(Icons.delete_outline_rounded),
                        onPressed: () => ref
                            .read(weighInQueueProvider)
                            .removeWeighIn(r.clientId),
                      ),
                    ],
                  )
                : null,
          ),
        for (final w in items.reversed)
          ListTile(
            key: tileKey(dateKey(w.date)),
            contentPadding: EdgeInsets.zero,
            title: Text(
              !numbersHidden && w.weightKg != null
                  ? '${_dateText(l10n, w.date)} · '
                        '${l10n.weightKgValue(formatDecimal(w.weightKg!))}'
                  : _dateText(l10n, w.date),
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  key: editKey(dateKey(w.date)),
                  tooltip: l10n.weightEdit,
                  icon: const Icon(Icons.edit_outlined),
                  onPressed: () async {
                    await showWeighInSheet(
                      context,
                      date: dateKey(w.date),
                      weightKg: numbersHidden ? null : w.weightKg,
                    );
                  },
                ),
                IconButton(
                  key: deleteKey(dateKey(w.date)),
                  tooltip: l10n.weightDelete,
                  icon: const Icon(Icons.delete_outline_rounded),
                  onPressed: () => _delete(context, ref, dateKey(w.date)),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
