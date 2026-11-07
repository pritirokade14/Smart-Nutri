import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/network/api_client.dart';
import '../data/favourites_repository.dart';

final favouritesRepositoryProvider = Provider<FavouritesRepository>(
  (ref) => FavouritesRepository(ref.watch(apiClientProvider).favourites),
);

/// The member's favourites, newest first. No automatic retry.
final favouritesProvider = FutureProvider.autoDispose
    .family<List<FavouriteOut>, String?>(
      (ref, memberId) =>
          ref.watch(favouritesRepositoryProvider).list(memberId: memberId),
      retry: (_, _) => null,
    );
