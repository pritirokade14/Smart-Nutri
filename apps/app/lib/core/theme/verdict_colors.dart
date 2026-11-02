import 'dart:ui' show Color;

import 'tokens.g.dart';

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
