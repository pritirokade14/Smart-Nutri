import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../data/methodology_repository.dart';

/// How long a loaded methodology is kept in memory (the API caches it for
/// the same hour).
const methodologyCacheFor = Duration(hours: 1);

/// The methodology in [language], kept for [methodologyCacheFor] after it
/// loads. A failure is not kept; the screen retries.
final methodologyProvider = FutureProvider.autoDispose
    .family<Methodology, String>((ref, language) async {
      final result = await ref
          .watch(methodologyRepositoryProvider)
          .get(language);
      final link = ref.keepAlive();
      final timer = Timer(methodologyCacheFor, link.close);
      ref.onDispose(timer.cancel);
      return result;
    }, retry: (_, _) => null);
