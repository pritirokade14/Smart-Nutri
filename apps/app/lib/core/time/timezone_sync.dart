import 'package:flutter_timezone/flutter_timezone.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

/// Tells the API the phone's time zone when it differs from the account's
/// (`meTimezonePut`). The zone decides which local day a log belongs to; the
/// app never works out a date itself. Any failure (no plugin answer, offline,
/// a refusal) is ignored: nothing is sent and the account keeps its zone.
Future<void> syncTimezone(
  MeOut me,
  MeClient client, {
  Future<String> Function()? localZone,
}) async {
  try {
    final zone = await (localZone ?? _deviceZone)();
    if (zone.isEmpty || zone == me.timezone) return;
    await client.meTimezonePut(body: TimezoneIn(timezone: zone));
  } on Object {
    // Ignored on purpose.
  }
}

Future<String> _deviceZone() async =>
    (await FlutterTimezone.getLocalTimezone()).identifier;
