import '../data/product_discovery_repository.dart';

Map<String, String> _refParams(String prefix, ProductRef? ref) {
  if (ref == null) return const {};
  final id = ref.productId;
  final code = ref.barcode;
  if (id != null) return {prefix: id};
  if (code != null) return {'${prefix}_barcode': code};
  return const {};
}

ProductRef? _refFrom(Map<String, String> q, String prefix) {
  final id = q[prefix];
  final code = q['${prefix}_barcode'];
  if (id != null && id.isNotEmpty) return (productId: id, barcode: null);
  if (code != null && code.isNotEmpty) return (productId: null, barcode: code);
  return null;
}

String _location(String path, Map<String, String> params) =>
    Uri(path: path, queryParameters: params.isEmpty ? null : params).toString();

/// `/compare?a=|a_barcode=&b=|b_barcode=&member_id=`.
String compareLocation(ProductRef a, ProductRef? b, {String? memberId}) =>
    _location('/compare', {
      ..._refParams('a', a),
      ..._refParams('b', b),
      'member_id': ?memberId,
    });

/// `/search`, or `/search?a=|a_barcode=&member_id=` to pick the second
/// product of a compare.
String searchLocation({ProductRef? compareWith, String? memberId}) =>
    _location('/search', {
      ..._refParams('a', compareWith),
      if (compareWith != null) 'member_id': ?memberId,
    });

/// `/result?product_id=` for our products, else `/result?barcode=`.
String resultLocation(ProductRef ref) => _location(
  '/result',
  ref.productId != null
      ? {'product_id': ref.productId!}
      : {'barcode': ?ref.barcode},
);

/// The parsed `/compare` and `/search` query.
({ProductRef? a, ProductRef? b, String? memberId}) discoveryQuery(
  Map<String, String> q,
) => (
  a: _refFrom(q, 'a'),
  b: _refFrom(q, 'b'),
  memberId: (q['member_id']?.isEmpty ?? true) ? null : q['member_id'],
);
