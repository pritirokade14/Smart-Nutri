import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../meals/presentation/meals_providers.dart';
import '../data/diary_repository.dart';
import '../domain/diary_dates.dart';
import 'copy_sheet.dart';
import 'diary_providers.dart';

enum _DayAction { copyYesterday, copyDay, partial, manage }

/// The day menu: copy yesterday, copy a day, mark as partly logged.
/// Everything here needs a connection (Ruling E19).
class DayMenu extends ConsumerWidget {
  const DayMenu({super.key, required this.day});

  final DiaryDayOut day;

  static const menuKey = Key('diary-day-menu');
  static const copyYesterdayKey = Key('diary-copy-yesterday');
  static const copyDayKey = Key('diary-copy-day');
  static const partialKey = Key('diary-mark-partial');
  static const manageKey = Key('diary-manage-meals');

  Future<void> _copyDay(BuildContext context) async {
    final shown = parseDateKey(dateKey(day.date))!;
    final picked = await showDatePicker(
      context: context,
      initialDate: shown,
      firstDate: DateTime(shown.year - 1, shown.month, shown.day),
      lastDate: DateTime(shown.year, shown.month, shown.day),
    );
    if (picked == null || !context.mounted) return;
    await showCopySheet(
      context,
      fromDate: dateKey(picked),
      toDate: dateKey(day.date),
    );
  }

  Future<void> _togglePartial(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final marking = !day.partialLogged;
    try {
      await ref
          .read(diaryRepositoryProvider)
          .setPartial(dateKey(day.date), marking);
      ref.read(mealsRevisionProvider.notifier).bump();
      // Explains what the mark does.
      if (marking) {
        messenger.showSnackBar(SnackBar(content: Text(l10n.diaryPartialNote)));
      }
    } on DiaryFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return PopupMenuButton<_DayAction>(
      key: menuKey,
      onSelected: (a) {
        switch (a) {
          case _DayAction.copyYesterday:
            showCopySheet(
              context,
              fromDate: shiftDateKey(dateKey(day.date), -1),
              toDate: dateKey(day.date),
            );
          case _DayAction.copyDay:
            _copyDay(context);
          case _DayAction.partial:
            _togglePartial(context, ref);
          case _DayAction.manage:
            context.push('/diary/meals');
        }
      },
      itemBuilder: (_) => [
        PopupMenuItem(
          key: copyYesterdayKey,
          value: _DayAction.copyYesterday,
          child: Text(l10n.diaryCopyYesterday),
        ),
        PopupMenuItem(
          key: copyDayKey,
          value: _DayAction.copyDay,
          child: Text(l10n.diaryCopyDay),
        ),
        CheckedPopupMenuItem(
          key: partialKey,
          value: _DayAction.partial,
          checked: day.partialLogged,
          child: Text(l10n.diaryMarkPartial),
        ),
        PopupMenuItem(
          key: manageKey,
          value: _DayAction.manage,
          child: Text(l10n.diarySlotsManage),
        ),
      ],
    );
  }
}
