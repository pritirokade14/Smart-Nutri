import 'package:intl/intl.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../scan/domain/number_text.dart';

/// A whole number with the locale's digit grouping ("2,760"). Display only.
String formatWhole(AppLocalizations l10n, num value) =>
    NumberFormat.decimalPattern(l10n.localeName).format(value.round());

/// A decimal exactly as the API sent it ("59.3", "0.37"), no rounding.
String formatDecimal(num value) => formatForDisplay(value);

/// `{value} kcal`.
String kcalText(AppLocalizations l10n, num value) =>
    l10n.targetsKcalValue(formatWhole(l10n, value));

/// `{value} g`.
String gramsText(AppLocalizations l10n, num value) =>
    l10n.targetsGValue(formatDecimal(value));
