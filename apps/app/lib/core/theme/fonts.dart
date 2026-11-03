import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Mukta (Ek Type) covers Latin and Devanagari, so English, Hindi and Marathi
/// render in one family with matching metrics. Bundled in `assets/fonts`.
const snFontFamily = 'Mukta';

/// Lists the bundled font's SIL Open Font License on the licences page.
void registerFontLicenses() {
  LicenseRegistry.addLicense(() async* {
    final text = await rootBundle.loadString('assets/fonts/mukta/OFL.txt');
    yield LicenseEntryWithLineBreaks(const [snFontFamily], text);
  });
}
