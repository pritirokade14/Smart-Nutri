import '../../../core/l10n/app_localizations.dart';

/// The display name of a meal slot: the user's own label exactly as typed
/// (user text, never translated), else the translated default `labelKey`.
String slotLabel(
  AppLocalizations l10n, {
  String? labelKey,
  String? customLabel,
}) {
  final custom = customLabel;
  if (custom != null && custom.trim().isNotEmpty) return custom;
  return switch (labelKey) {
    'diary.slot.breakfast' => l10n.diarySlotBreakfast,
    'diary.slot.lunch' => l10n.diarySlotLunch,
    'diary.slot.snack' => l10n.diarySlotSnack,
    'diary.slot.dinner' => l10n.diarySlotDinner,
    _ => labelKey ?? '',
  };
}
