import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../foods/data/foods_repository.dart';
import '../data/favourites_repository.dart';
import 'favourites_providers.dart';

/// A star that stars or unstars one food. [favouriteId] is the API's
/// `favourite_id` (null: not a favourite). It adds with the given default
/// portion and deletes by id; a refusal shows its message and leaves the star
/// as it was. Nothing about the food is sent to analytics.
class FavouriteStar extends ConsumerStatefulWidget {
  const FavouriteStar({
    super.key,
    required this.food,
    required this.favouriteId,
    this.memberId,
    this.quantity,
    this.unit,
    this.onChanged,
  });

  final FoodRef food;
  final String? favouriteId;
  final String? memberId;
  final num? quantity;
  final String? unit;
  final void Function(String? favouriteId)? onChanged;

  static Key starKey(String id) => Key('favourite-star-$id');

  @override
  ConsumerState<FavouriteStar> createState() => _FavouriteStarState();
}

class _FavouriteStarState extends ConsumerState<FavouriteStar> {
  late String? _id = widget.favouriteId;
  bool _busy = false;

  Future<void> _toggle() async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final repo = ref.read(favouritesRepositoryProvider);
    setState(() => _busy = true);
    try {
      if (_id != null) {
        await repo.delete(_id!);
        _id = null;
      } else {
        final f = await repo.addFood(
          widget.food,
          memberId: widget.memberId,
          quantity: widget.quantity,
          unit: widget.unit,
        );
        _id = f.id;
        messenger.showSnackBar(SnackBar(content: Text(l10n.favouritesAdded)));
      }
      ref.invalidate(favouritesProvider(widget.memberId));
      widget.onChanged?.call(_id);
    } on FavouritesFailure catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(localizedErrorCode(l10n, e.code))),
      );
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final on = _id != null;
    return IconButton(
      key: FavouriteStar.starKey('${widget.food.kind.json}-${widget.food.id}'),
      tooltip: on ? l10n.favouritesRemove : l10n.favouritesAdd,
      isSelected: on,
      icon: const Icon(Icons.star_border_rounded),
      selectedIcon: const Icon(Icons.star_rounded),
      onPressed: _busy ? null : _toggle,
    );
  }
}
