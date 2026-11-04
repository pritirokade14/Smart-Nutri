import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/product_discovery_repository.dart';

typedef AlternativesQuery = ({
  ProductRef product,
  String? memberId,
  AlternativesSort sort,
});

typedef SearchQuery = ({String q, SearchSort sort, String? memberId});

typedef CompareQuery = ({ProductRef a, ProductRef b, String? memberId});

/// The shortest and longest search the API accepts (after trimming).
const searchMinLength = 3;
const searchMaxLength = 80;

/// No automatic retry anywhere here: screens show the failure and the user
/// retries explicitly.
final alternativesProvider = FutureProvider.autoDispose
    .family<AlternativesOut, AlternativesQuery>(
      (ref, q) => ref
          .watch(productDiscoveryRepositoryProvider)
          .alternatives(q.product, memberId: q.memberId, sort: q.sort),
      retry: (_, _) => null,
    );

final productSearchProvider = FutureProvider.autoDispose
    .family<List<SearchHit>, SearchQuery>(
      (ref, q) => ref
          .watch(productDiscoveryRepositoryProvider)
          .search(q.q, sort: q.sort, memberId: q.memberId),
      retry: (_, _) => null,
    );

final compareProvider = FutureProvider.autoDispose
    .family<CompareOut, CompareQuery>(
      (ref, q) => ref
          .watch(productDiscoveryRepositoryProvider)
          .compare(q.a, q.b, memberId: q.memberId),
      retry: (_, _) => null,
    );
