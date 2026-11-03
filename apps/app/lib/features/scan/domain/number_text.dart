/// Text <-> number for the confirm form, identical to the web client
/// (`apps/web/src/features/scan/lib/draftSchema.ts`). An unedited field sends
/// the API's number unchanged.
library;

/// The exact value for an input, never rounded to fewer digits than printed
/// (0.04 stays "0.04"). Floating-point noise beyond 12 significant digits is
/// dropped for display only (as the web's `toPrecision(12)`).
String formatForDisplay(num value) {
  if (!value.isFinite) return '';
  final clean = double.parse(value.toStringAsPrecision(12));
  if (clean == clean.truncateToDouble() && clean.abs() < 1e15) {
    return clean.toInt().toString();
  }
  return clean.toString();
}

/// A plain non-negative decimal: "12", "12.5", "12." or ".5".
final _decimal = RegExp(r'^(\d+(\.\d*)?|\.\d+)$');

/// Parses a typed amount. Blank is a valid null (not printed), never 0.
/// Anything other than a plain non-negative decimal ("1,5", "-1", "abc") is
/// rejected (`ok: false`), never guessed.
({bool ok, num? value}) parseNumber(String text) {
  final s = text.trim();
  if (s.isEmpty) return (ok: true, value: null);
  if (!_decimal.hasMatch(s)) return (ok: false, value: null);
  final value = num.tryParse(
    s.endsWith('.') ? s.substring(0, s.length - 1) : s,
  );
  if (value == null || !value.isFinite) return (ok: false, value: null);
  return (ok: true, value: value);
}
