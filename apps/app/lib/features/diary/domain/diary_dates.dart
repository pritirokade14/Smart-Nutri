/// A calendar date as the API writes it (`2026-11-07`). Formatting only: the
/// app never works out which day is "today" or where a day ends (Ruling E8).
String dateKey(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-'
    '${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

/// The calendar date [key] as a `DateTime` for the generated client (a date
/// query, which the API reads back as the same date).
DateTime? parseDateKey(String? key) {
  if (key == null) return null;
  final p = key.split('-');
  if (p.length != 3) return null;
  final y = int.tryParse(p[0]), m = int.tryParse(p[1]), d = int.tryParse(p[2]);
  if (y == null || m == null || d == null) return null;
  return DateTime.utc(y, m, d);
}

/// The calendar date [days] before or after [key] (the date switcher's
/// previous and next).
String shiftDateKey(String key, int days) => dateKey(
  DateTime.utc(
    parseDateKey(key)!.year,
    parseDateKey(key)!.month,
    parseDateKey(key)!.day + days,
  ),
);
