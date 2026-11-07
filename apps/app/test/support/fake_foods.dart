import 'package:smartnutri_api/src/export.dart';

FoodUnitOut unitOut(
  String code,
  num gramsPerUnit, {
  FoodUnitOutKind kind = FoodUnitOutKind.count,
  num? ml,
  bool userOverride = false,
}) => FoodUnitOut(
  code: code,
  gramsPerUnit: gramsPerUnit,
  kind: kind,
  ml: ml,
  source: userOverride
      ? FoodUnitOutSource.portionUser
      : FoodUnitOutSource.portionGlobal,
  userOverride: userOverride,
);

/// Cooked toor dal per the shared `units/conversions.json` (per 100 g).
NutrientSnapshot dalPer100() => const NutrientSnapshot(
  carbsG: 15,
  energyKcal: 120,
  fatG: 3,
  fibreG: 4,
  proteinG: 7,
  saltG: 0.5,
  satFatG: null,
  sugarsG: 2.5,
);

NutrientSnapshot allNull() => const NutrientSnapshot(
  carbsG: null,
  energyKcal: null,
  fatG: null,
  fibreG: null,
  proteinG: null,
  saltG: null,
  satFatG: null,
  sugarsG: null,
);

FoodDetailOut foodDetail({
  String id = 'f1',
  String name = 'Toor dal, cooked',
  FoodDetailOutKind kind = FoodDetailOutKind.food,
  NutrientSnapshot? per100,
  List<FoodUnitOut>? units,
  String defaultUnit = 'katori',
  List<String> settableUnits = const [],
  List<String> attributions = const ['attribution.usda_fdc'],
  DishOut? dish,
  bool reviewPending = true,
  bool hideEnergy = false,
  bool hideMacros = false,
}) => FoodDetailOut(
  attribution: null,
  attributions: attributions,
  basis: FoodDetailOutBasis.g,
  brand: null,
  defaultUnit: defaultUnit,
  dish: dish,
  id: id,
  kind: kind,
  licence: null,
  name: name,
  numbersHidden: NumbersHidden(energy: hideEnergy, macros: hideMacros),
  per100: per100 ?? dalPer100(),
  reviewPending: reviewPending,
  servingG: null,
  settableUnits: settableUnits,
  units:
      units ??
      [
        unitOut('g', 1, kind: FoodUnitOutKind.mass),
        unitOut('katori', 142, kind: FoodUnitOutKind.volume, ml: 200),
        unitOut('katori_medium', 110.05, kind: FoodUnitOutKind.volume, ml: 155),
      ],
);

FoodHit foodHit(
  String id,
  String name, {
  FoodHitKind kind = FoodHitKind.food,
  FoodHitGroup group = FoodHitGroup.indian,
  bool isDish = false,
  List<String> attributions = const ['attribution.usda_fdc'],
}) => FoodHit(
  attribution: null,
  attributions: attributions,
  brand: null,
  grade: null,
  group: group,
  id: id,
  isDish: isDish,
  kind: kind,
  name: name,
);

/// Records calls. `details` answers `foodsGet` by id.
class FakeFoodsClient implements FoodsClient {
  FakeFoodsClient({
    FoodSearchOut? search,
    Map<String, FoodDetailOut>? details,
    this.putError,
  }) : searchOut =
           search ??
           FoodSearchOut(
             failedSources: const [],
             items: const [],
             partial: false,
           ),
       details = details ?? {'f1': foodDetail()};

  FoodSearchOut searchOut;
  final Map<String, FoodDetailOut> details;
  Object? putError;
  final queries = <String>[];
  final gets = <String>[];
  final puts = <(String, String, num)>[];
  final deletes = <(String, String)>[];

  @override
  Future<FoodSearchOut> foodsSearch({
    required String q,
    int? limit = 20,
    List<SearchKind>? kinds,
  }) async {
    queries.add(q);
    return searchOut;
  }

  @override
  Future<List<UnitOut>> foodsUnitsList() async => const [];

  @override
  Future<FoodDetailOut> foodsGet({
    required FoodKindPath kind,
    required String id,
    String? memberId,
  }) async {
    gets.add(id);
    return details[id]!;
  }

  @override
  Future<FoodDetailOut> foodsPortionPut({
    required FoodKindPath kind,
    required String id,
    required String unit,
    required PortionIn body,
    String? memberId,
  }) async {
    final e = putError;
    if (e != null) throw e;
    puts.add((id, unit, body.gramsPerUnit));
    final d = details[id]!;
    final units = [
      for (final u in d.units)
        if (u.code != unit) u,
      unitOut(unit, body.gramsPerUnit, userOverride: true),
    ];
    details[id] = foodDetail(
      id: id,
      name: d.name,
      units: units,
      defaultUnit: d.defaultUnit,
      settableUnits: [
        for (final s in d.settableUnits)
          if (s != unit) s,
      ],
      per100: d.per100,
    );
    return details[id]!;
  }

  @override
  Future<void> foodsPortionDelete({
    required FoodKindPath kind,
    required String id,
    required String unit,
  }) async {
    deletes.add((id, unit));
    final d = details[id]!;
    details[id] = foodDetail(
      id: id,
      name: d.name,
      units: [
        for (final u in d.units)
          if (u.code == unit) unitOut(unit, 142) else u,
      ],
      defaultUnit: d.defaultUnit,
      per100: d.per100,
    );
  }
}
