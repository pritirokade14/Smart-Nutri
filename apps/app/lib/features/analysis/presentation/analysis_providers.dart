import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/analysis_repository.dart';

/// Exactly one of [barcode] and [productId] is set.
typedef AnalyzeQuery = ({String? barcode, String? productId, String language});

/// The analysis for one scanned barcode or one saved product. No automatic
/// retry: the screen shows the failure and the user retries explicitly.
final analyzeResultProvider = FutureProvider.autoDispose
    .family<AnalyzeOut, AnalyzeQuery>((ref, q) {
      final repo = ref.watch(analysisRepositoryProvider);
      final id = q.productId;
      return id != null
          ? repo.analyzeProduct(id, language: q.language)
          : repo.analyzeBarcode(q.barcode ?? '', language: q.language);
    }, retry: (_, _) => null);
