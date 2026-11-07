import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../domain/diary_dates.dart';

/// The route of the Diary for [date] (null: the account's today).
String diaryPath(String? date) => date == null ? '/diary' : '/diary?date=$date';

/// Previous and next day, and a date picker. Dates are the API's
/// (`DiaryDayOut.date` and `today`); the next day is disabled on `today`.
class DayHeader extends StatelessWidget {
  const DayHeader({super.key, required this.day});

  final DiaryDayOut day;

  static const prevKey = Key('diary-prev-day');
  static const nextKey = Key('diary-next-day');
  static const dateKeyKey = Key('diary-date');

  Future<void> _pick(BuildContext context) async {
    final today = DateTime(day.today.year, day.today.month, day.today.day);
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(day.date.year, day.date.month, day.date.day),
      firstDate: DateTime(today.year - 1, today.month, today.day),
      lastDate: today,
    );
    if (picked == null || !context.mounted) return;
    final key = dateKey(picked);
    context.go(diaryPath(key == dateKey(day.today) ? null : key));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final date = dateKey(day.date);
    final today = dateKey(day.today);
    final isToday = date == today;
    final label = isToday
        ? l10n.diaryToday
        : (DateFormat.MMMEd(l10n.localeName)..useNativeDigits = false).format(
            DateTime(day.date.year, day.date.month, day.date.day),
          );
    return Row(
      children: [
        IconButton(
          key: prevKey,
          tooltip: l10n.diaryPrevDay,
          icon: const Icon(Icons.chevron_left_rounded),
          onPressed: () => context.go(diaryPath(shiftDateKey(date, -1))),
        ),
        Expanded(
          child: TextButton(
            onPressed: () => _pick(context),
            child: Text(
              label,
              key: dateKeyKey,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
        ),
        IconButton(
          key: nextKey,
          tooltip: l10n.diaryNextDay,
          icon: const Icon(Icons.chevron_right_rounded),
          onPressed: isToday
              ? null
              : () {
                  final next = shiftDateKey(date, 1);
                  context.go(diaryPath(next == today ? null : next));
                },
        ),
      ],
    );
  }
}
