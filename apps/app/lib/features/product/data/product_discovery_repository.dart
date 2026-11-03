import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';

/// A product reference: exactly one of [productId] (our product) and
/// [barcode] (Open Food Facts) is set.
typedef ProductRef = ({String? productId, String? barcode});

/// A failed alternatives, search or compare call. [code] is the API
/// `error.code` (`off_unavailable`, `product_not_found`, ...), `network`, or
/// null; screens map it with `localizedErrorCode`.
class DiscoveryFailure implements Exception {
  const DiscoveryFailure(this.code, [this.cause]);

  final String? code;
  final Object? cause;

  static Future<T> guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on Object catch (e) {
      throw DiscoveryFailure(apiErrorCode(e), e);
    }
  }

  @override
  String toString() => 'DiscoveryFailure($code)';
}

/// Wraps the generated `ProductsClient` routes for alternatives, search and
/// compare. Returns the API bodies unchanged: grades, `member_status` and
/// `better` come only from the API.
class ProductDiscoveryRepository {
  ProductDiscoveryRepository(this._client);

  final ProductsClient _client;

  /// Healthier options in the same category (`member_id` optional).
  Future<AlternativesOut> alternatives(ProductRef ref, {String? memberId}) {
    final id = ref.productId;
    final code = ref.barcode;
    return DiscoveryFailure.guard(
      () => id != null
          ? _client.productsAlternatives(productId: id, memberId: memberId)
          : _client.productsAlternativesByBarcode(
              code: code ?? '',
              memberId: memberId,
            ),
    );
  }

  /// Our catalogue plus Open Food Facts; [query] is 2–80 characters.
  Future<List<SearchHit>> search(String query, {int limit = 20}) =>
      DiscoveryFailure.guard(
        () => _client.productsSearch(q: query.trim(), limit: limit),
      );

  Future<CompareOut> compare(ProductRef a, ProductRef b, {String? memberId}) =>
      DiscoveryFailure.guard(
        () => _client.productsCompare(
          a: a.productId,
          aBarcode: a.productId == null ? a.barcode : null,
          b: b.productId,
          bBarcode: b.productId == null ? b.barcode : null,
          memberId: memberId,
        ),
      );
}

final productDiscoveryRepositoryProvider = Provider<ProductDiscoveryRepository>(
  (ref) => ProductDiscoveryRepository(ref.watch(apiClientProvider).products),
);
