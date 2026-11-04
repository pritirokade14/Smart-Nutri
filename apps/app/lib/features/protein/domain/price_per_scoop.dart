/// Price per scoop, computed on this phone only from a price the user typed.
/// It is never stored, logged, sent to the API, put in a URL or tracked.
library;

/// `price * servingSizeG / packSizeG`, rounded half up to 2 decimals; null
/// when any input is missing or not above 0 (shared fixture
/// `packages/test-fixtures/protein/price_per_scoop.json`).
num? pricePerScoop(num? price, num? packSizeG, num? servingSizeG) {
  if (price == null || packSizeG == null || servingSizeG == null) return null;
  if (price <= 0 || packSizeG <= 0 || servingSizeG <= 0) return null;
  final raw = price * servingSizeG / packSizeG;
  // Positive, so `round` is half up; the nudge keeps x.xx5 from rounding
  // down through a binary fraction.
  return (raw * 100 + 1e-9).round() / 100;
}
