import 'package:smartnutri_ai/core/platform/app_settings.dart';

/// An [AppSettings] whose "permanently denied" answer is fixed.
class FakeAppSettings extends AppSettings {
  FakeAppSettings({this.permanent = true});

  final bool permanent;
  int opened = 0;
  final denied = <String>[];

  @override
  Future<bool> noteDenied(String permission) async {
    denied.add(permission);
    return permanent;
  }

  @override
  Future<void> open() async => opened++;
}
