import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../data/favourites_repository.dart';
import 'favourites_providers.dart';

/// Saves a slot of a day as a favourite meal. The name is user text: sent as
/// typed, never translated, never in analytics.
Future<void> showSaveMealFavouriteSheet(
  BuildContext context, {
  required String fromDate,
  required String fromSlotId,
  String? memberId,
}) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => SaveMealFavouriteSheet(
    fromDate: fromDate,
    fromSlotId: fromSlotId,
    memberId: memberId,
  ),
);

class SaveMealFavouriteSheet extends ConsumerStatefulWidget {
  const SaveMealFavouriteSheet({
    super.key,
    required this.fromDate,
    required this.fromSlotId,
    this.memberId,
  });

  final String fromDate;
  final String fromSlotId;
  final String? memberId;

  static const nameKey = Key('save-meal-name');
  static const saveKey = Key('save-meal-save');
  static const maxLength = 40;

  @override
  ConsumerState<SaveMealFavouriteSheet> createState() =>
      _SaveMealFavouriteSheetState();
}

class _SaveMealFavouriteSheetState
    extends ConsumerState<SaveMealFavouriteSheet> {
  final _name = TextEditingController();

  /// One per sheet: a retry reuses it.
  final String _clientId = const Uuid().v4();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  bool get _valid =>
      _name.text.trim().isNotEmpty &&
      _name.text.runes.length <= SaveMealFavouriteSheet.maxLength;

  Future<void> _save() async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(favouritesRepositoryProvider)
          .addMeal(
            fromDate: widget.fromDate,
            fromSlotId: widget.fromSlotId,
            // Exactly as typed.
            name: _name.text,
            clientId: _clientId,
            memberId: widget.memberId,
          );
      ref.invalidate(favouritesProvider(widget.memberId));
      messenger.showSnackBar(SnackBar(content: Text(l10n.favouritesAdded)));
      if (mounted) nav.pop();
    } on FavouritesFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Padding(
      padding: EdgeInsets.only(
        left: SnTokens.space4,
        right: SnTokens.space4,
        bottom: MediaQuery.viewInsetsOf(context).bottom + SnTokens.space4,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            l10n.favouritesSaveMeal,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: SnTokens.space3),
          TextField(
            key: SaveMealFavouriteSheet.nameKey,
            controller: _name,
            enabled: !_busy,
            autofocus: true,
            onChanged: (_) => setState(() {}),
            decoration: InputDecoration(
              labelText: l10n.favouritesMealName,
              helperText: l10n.favouritesMealNameHint,
              counterText: '',
            ),
          ),
          const SizedBox(height: SnTokens.space3),
          if (_error != null) ...[
            InlineErrorBanner(message: _error!),
            const SizedBox(height: SnTokens.space2),
          ],
          PrimaryButton(
            buttonKey: SaveMealFavouriteSheet.saveKey,
            label: l10n.favouritesSaveMeal,
            icon: Icons.star_rounded,
            busy: _busy,
            onPressed: _valid ? _save : null,
          ),
        ],
      ),
    );
  }
}
