import 'dart:ui' show Color;

import 'sn_colors.dart';
import 'tokens.g.dart';

/// The four engine statuses, in display-safety order.
const verdictStatuses = {'ok', 'caution', 'unknown', 'avoid'};

/// A status string this build can show. Anything it does not recognise is
/// shown as `unknown` (grey, "Label unclear"), never as `ok`.
String safeVerdictStatus(String status) =>
    verdictStatuses.contains(status) ? status : 'unknown';

/// Explicit verdict colours. The Material ColorScheme is deliberately neutral,
/// so verdict colours only ever come from here. `unknown` is never green.
Color verdictColor(String status) {
  switch (status) {
    case 'ok':
      return SnTokens.verdictOk;
    case 'caution':
      return SnTokens.verdictCaution;
    case 'unknown':
      return SnTokens.verdictUnknown;
    case 'avoid':
      return SnTokens.verdictAvoid;
  }
  throw ArgumentError.value(status, 'status', 'Unknown verdict status');
}

/// The colours for one verdict in the current palette: the solid colour, the
/// tinted card surface and the text/icon colour drawn on the solid colour.
typedef VerdictTone = ({Color color, Color surface, Color onColor});

/// [verdictColor] for the given palette (light or dark). Throws on a status
/// string it does not know, like [verdictColor]; pass it through
/// [safeVerdictStatus] first.
VerdictTone verdictTone(SnColors c, String status) => switch (status) {
  'ok' => (
    color: c.verdictOk,
    surface: c.verdictOkSurface,
    onColor: c.onVerdict,
  ),
  'caution' => (
    color: c.verdictCaution,
    surface: c.verdictCautionSurface,
    onColor: c.onVerdict,
  ),
  'unknown' => (
    color: c.verdictUnknown,
    surface: c.verdictUnknownSurface,
    onColor: c.onVerdict,
  ),
  'avoid' => (
    color: c.verdictAvoid,
    surface: c.verdictAvoidSurface,
    onColor: c.onVerdict,
  ),
  _ => throw ArgumentError.value(status, 'status', 'Unknown verdict status'),
};
