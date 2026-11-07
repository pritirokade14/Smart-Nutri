/// One "I ate this" log before it is sent. Exactly one of [productId] (our
/// product), [barcode] (Open Food Facts), [foodId] (a generic food or dish)
/// and [quickEnergyKcal] (a quick add) is the source; a food has exactly one
/// of [grams], [servings] and [quantity] with [unit].
class MealDraft {
  const MealDraft({
    required this.memberId,
    required this.eatenAt,
    this.productId,
    this.barcode,
    this.grams,
    this.servings,
    this.foodId,
    this.customFoodId,
    this.recipeId,
    this.quantity,
    this.unit,
    this.mealSlotId,
    this.localDate,
    this.quickName,
    this.quickEnergyKcal,
    this.quickProteinG,
    this.quickFatG,
    this.quickCarbsG,
    this.quickFibreG,
    this.displayName,
  });

  final String memberId;
  final String? productId;
  final String? barcode;
  final num? grams;
  final num? servings;

  /// A generic food or dish (`foods.id`).
  final String? foodId;

  /// One of the account's own custom foods or recipes.
  final String? customFoodId;
  final String? recipeId;

  /// A household-unit portion: [quantity] of [unit] (a unit code). Sent
  /// instead of grams and servings; the API converts it.
  final num? quantity;
  final String? unit;
  final DateTime eatenAt;

  /// The chosen slot, or null (the API picks one).
  final String? mealSlotId;

  /// A past day (`2026-11-06`); sent instead of [eatenAt].
  final String? localDate;

  /// Quick add fields. A blank is null, never 0.
  final String? quickName;
  final num? quickEnergyKcal;
  final num? quickProteinG;
  final num? quickFatG;
  final num? quickCarbsG;
  final num? quickFibreG;

  /// The name of the pending row ("waiting to sync").
  final String? displayName;

  bool get isQuick => quickEnergyKcal != null;
}
