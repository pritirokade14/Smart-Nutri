import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/analysis_repository.dart';

typedef AnalyzeQuery = ({String barcode, String language});

/// The analysis for one scanned barcode. No automatic retry: the screen shows
/// the failure and the user retries explicitly.
final analyzeResultProvider = FutureProvider.autoDispose
    .family<AnalyzeOut, AnalyzeQuery>(
      (ref, q) => ref
          .watch(analysisRepositoryProvider)
          .analyzeBarcode(q.barcode, language: q.language),
      retry: (_, _) => null,
    );
