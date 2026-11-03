/// One "I ate this" log before it is sent. Exactly one of [productId] (our
/// product) and [barcode] (Open Food Facts) is set, and exactly one of
/// [grams] and [servings].
class MealDraft {
  const MealDraft({
    required this.memberId,
    required this.eatenAt,
    this.productId,
    this.barcode,
    this.grams,
    this.servings,
  });

  final String memberId;
  final String? productId;
  final String? barcode;
  final num? grams;
  final num? servings;
  final DateTime eatenAt;
}
