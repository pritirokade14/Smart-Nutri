import 'package:flutter_test/flutter_test.dart';
import 'package:smartnutri_ai/features/scan/domain/barcode.dart';

void main() {
  test('strips spaces', () {
    expect(normalizeBarcode(' 8901 0632 0108 9 '), '8901063201089');
  });
  test('strips hyphens', () {
    expect(normalizeBarcode('8901-0632-0108-9'), '8901063201089');
  });
  test('keeps leading zero on 12-digit UPC', () {
    expect(normalizeBarcode('012345678905'), '012345678905');
  });
  test('accepts 8 and 14 digits', () {
    expect(normalizeBarcode('12345670'), '12345670');
    expect(normalizeBarcode('12345678901231'), '12345678901231');
  });
  test('rejects non-digits and wrong lengths', () {
    expect(normalizeBarcode('abc123'), isNull);
    expect(normalizeBarcode('1234567'), isNull);
    expect(normalizeBarcode('123456789012345'), isNull);
    expect(normalizeBarcode('12345678a9012'), isNull);
    expect(normalizeBarcode(''), isNull);
  });
}
