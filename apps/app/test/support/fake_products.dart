import 'package:smartnutri_api/src/export.dart';

import 'fake_meals.dart' show apiError;

AlternativeOut alternative({
  required String name,
  String? barcode,
  String? productId,
  NutriScoreGrade grade = NutriScoreGrade.b,
  num? sugarsG = 4,
  MemberStatus? memberStatus,
  String? brand = 'Brand',
}) => AlternativeOut(
  attribution: barcode == null ? null : 'attribution.off',
  barcode: barcode,
  brand: brand,
  grade: grade,
  highIn: const [],
  imageUrl: null,
  memberStatus: memberStatus,
  name: name,
  productId: productId,
  proteinG: null,
  proteinPer100kcal: null,
  sugarsG: sugarsG,
);

NutrientsOut nutrients({
  num? energyKcal = 450,
  num? sugarsG = 20,
  num? saltG = 1,
  num? satFatG = 7,
  num? proteinG = 6,
  num? fiberG,
}) => NutrientsOut(
  carbsG: null,
  energyKcal: energyKcal,
  fatG: null,
  fiberG: fiberG,
  proteinG: proteinG,
  saltG: saltG,
  satFatG: satFatG,
  sodiumMg: null,
  sugarsG: sugarsG,
);

CompareSide compareSide({
  required String name,
  String? barcode,
  String? productId,
  NutriScoreGrade? grade,
  NutrientsOut? per100g,
  MemberStatus? memberStatus,
}) => CompareSide(
  attribution: barcode == null ? null : 'attribution.off',
  barcode: barcode,
  brand: null,
  grade: grade,
  highIn: const [],
  memberStatus: memberStatus,
  name: name,
  per100g: per100g ?? nutrients(),
  productId: productId,
  proteinPer100kcal: null,
  proteinPerServingG: null,
  servingSizeG: null,
  sugarsPerServingG: null,
);

/// Records alternatives, search and compare calls. Every other route
/// throws.
class FakeProductsClient implements ProductsClient {
  final alternativesCalls = <(String?, String?, String?)>[];
  final alternativesSorts = <AlternativesSort?>[];
  final searches = <String>[];
  final searchCalls = <({String q, SearchSort? sort, String? memberId})>[];
  final compares = <Map<String, String?>>[];

  AlternativesOut alternativesOut = const AlternativesOut(
    items: [],
    reason: AlternativesOutReason.noBetterFound,
  );
  Object? alternativesError;
  List<SearchHit> hits = [];
  Object? searchError;
  CompareOut? compareOut;
  Object? compareError;

  @override
  Future<AlternativesOut> productsAlternatives({
    required String productId,
    AlternativesSort? sort = AlternativesSort.grade,
    String? memberId,
  }) async {
    alternativesCalls.add((productId, null, memberId));
    alternativesSorts.add(sort);
    if (alternativesError case final e?) throw e;
    return alternativesOut;
  }

  @override
  Future<AlternativesOut> productsAlternativesByBarcode({
    required String code,
    AlternativesSort? sort = AlternativesSort.grade,
    String? memberId,
  }) async {
    alternativesCalls.add((null, code, memberId));
    alternativesSorts.add(sort);
    if (alternativesError case final e?) throw e;
    return alternativesOut;
  }

  @override
  Future<List<SearchHit>> productsSearch({
    required String q,
    String? memberId,
    int? limit = 20,
    SearchSort? sort = SearchSort.relevance,
  }) async {
    searches.add(q);
    searchCalls.add((q: q, sort: sort, memberId: memberId));
    if (searchError case final e?) throw e;
    return hits;
  }

  @override
  Future<CompareOut> productsCompare({
    String? a,
    String? aBarcode,
    String? b,
    String? bBarcode,
    String? memberId,
  }) async {
    compares.add({
      'a': a,
      'a_barcode': aBarcode,
      'b': b,
      'b_barcode': bBarcode,
      'member_id': memberId,
    });
    if (compareError case final e?) throw e;
    final out = compareOut;
    if (out == null) throw apiError(404, 'product_not_found');
    return out;
  }

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}
