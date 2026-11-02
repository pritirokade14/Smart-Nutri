/// Normalizes a barcode the same way the API does: strips spaces and hyphens,
/// keeps leading zeros, accepts digits only with length 8, 12, 13 or 14.
String? normalizeBarcode(String raw) {
  final s = raw.replaceAll(RegExp(r'[\s-]'), '');
  if (!RegExp(r'^\d+$').hasMatch(s)) return null;
  const allowed = {8, 12, 13, 14};
  return allowed.contains(s.length) ? s : null;
}
