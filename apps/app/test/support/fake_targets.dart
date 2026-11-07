import 'package:smartnutri_api/src/export.dart';

import 'fixtures.dart';

/// A stored settings row the way the API returns it.
GoalSettingsOut goalSettingsOut({
  String direction = 'maintain',
  String activity = 'light',
  String numbersDisplay = 'show',
  num? ratePct,
  bool pregnant = false,
}) => GoalSettingsOut.fromJson({
  'member_id': 'p1',
  'direction': direction,
  'activity_level': activity,
  'rate_pct_bw_per_week': ratePct,
  'target_weight_kg': null,
  'sex_reference': null,
  'pregnant_or_breastfeeding': pregnant,
  'fat_pct_energy': null,
  'energy_mode': 'formula',
  'numbers_display': numbersDisplay,
  'summary_view': 'remaining',
  'updated_at': '2026-11-07T08:00:00Z',
});

/// `TargetsClient` over the golden target files. Records every call.
class FakeTargetsClient implements TargetsClient {
  FakeTargetsClient({String today = 'none', this.settings}) {
    this.today = targetsFixture(today);
  }

  late TargetsOut today;
  GoalSettingsOut? settings;

  /// What `targets_preview` answers (defaults to [today]).
  TargetsOut? previewResult;

  /// Computes the preview from the body sent (overrides [previewResult]).
  TargetsOut Function(TargetsPreviewIn body)? previewFor;

  /// What the next `targetsGet` answers after `targets_display_put`.
  TargetsOut Function(String display)? todayForDisplay;

  final gets = <String?>[];
  final previews = <TargetsPreviewIn>[];
  final puts = <GoalSettingsIn>[];
  final displays = <DisplayIn>[];
  final resets = <String?>[];

  Object? getError;

  /// Thrown by the next `targetsDisplayPut`.
  Object? displayError;
  Object? settingsGetError;

  /// Thrown by the next preview calls, in order.
  final previewErrors = <Object>[];
  final putErrors = <Object>[];

  @override
  Future<TargetsOut> targetsGet({String? memberId, DateTime? date}) async {
    gets.add(memberId);
    if (getError case final e?) throw e;
    return today;
  }

  @override
  Future<GoalSettingsOut?> targetsSettingsGet({String? memberId}) async {
    if (settingsGetError case final e?) throw e;
    return settings;
  }

  @override
  Future<TargetsOut> targetsPreview({required TargetsPreviewIn body}) async {
    previews.add(body);
    if (previewErrors.isNotEmpty) throw previewErrors.removeAt(0);
    return previewFor?.call(body) ?? previewResult ?? today;
  }

  @override
  Future<TargetsOut> targetsSettingsPut({required GoalSettingsIn body}) async {
    puts.add(body);
    if (putErrors.isNotEmpty) throw putErrors.removeAt(0);
    settings = goalSettingsOut(
      direction: body.direction.json!,
      activity: body.activityLevel.json!,
      numbersDisplay: body.numbersDisplay.json!,
    );
    return previewResult ?? today;
  }

  @override
  Future<DisplayOut> targetsDisplayPut({required DisplayIn body}) async {
    displays.add(body);
    if (displayError case final e?) {
      displayError = null;
      throw e;
    }
    final s = settings ?? goalSettingsOut();
    final display = body.numbersDisplay?.json ?? s.numbersDisplay.json!;
    settings = goalSettingsOut(
      direction: s.direction.json!,
      activity: s.activityLevel.json!,
      numbersDisplay: display,
    );
    if (todayForDisplay case final f?) today = f(display);
    return DisplayOut(
      memberId: settings!.memberId,
      numbersDisplay: DisplayOutNumbersDisplay.fromJson(display),
      summaryView: DisplayOutSummaryView.fromJson(
        body.summaryView?.json ?? settings!.summaryView.json!,
      ),
      updatedAt: settings!.updatedAt,
    );
  }

  @override
  Future<void> targetsSettingsDelete({String? memberId}) async {
    resets.add(memberId);
    settings = null;
    today = targetsFixture('none');
  }
}
