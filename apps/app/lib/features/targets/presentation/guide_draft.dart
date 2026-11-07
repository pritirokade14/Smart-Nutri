import 'package:flutter/widgets.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../members/domain/member.dart';
import '../../scan/domain/number_text.dart';
import '../domain/direction_defaults.dart';

const sexOptions = ['female', 'male', 'other'];
const sexReferenceOptions = ['female', 'male', 'average'];
const activityLevels = ['sedentary', 'light', 'moderate', 'very'];
const directionOptions = ['lose', 'maintain', 'gain'];
const numbersDisplayOptions = ['show', 'hide_energy', 'hide_all'];

/// The daily-guide answers while the user edits them. The app only collects
/// answers; every number comes from the API (`targets_preview`).
class GuideDraft extends ChangeNotifier {
  final birthYear = TextEditingController();
  final height = TextEditingController();
  final weight = TextEditingController();
  final bodyFat = TextEditingController();
  final targetWeight = TextEditingController();

  /// `female`, `male`, `other`, or null for "not set".
  String? sex;

  /// The estimate to use when sex is `other` or not set.
  String sexReference = 'average';
  String? activity;
  String direction = 'maintain';

  /// The chosen pace in % of body weight per week (an API option), or null
  /// for the API's default.
  num? ratePct;

  /// `yes`, `no` or `prefer_not` (both of the first and last pause guides).
  String pregnancy = 'no';
  String numbersDisplay = 'show';

  /// What the account already stores, to tell "blank" from "never set".
  MemberOut? member;
  GoalSettingsOut? stored;

  /// Fields the API said are missing (member field names).
  Set<String> missing = {};

  void notify() => notifyListeners();

  /// Fills the answers from the member (body data) and the stored settings.
  void load(MemberOut m, GoalSettingsOut? s) {
    member = m;
    stored = s;
    birthYear.text = m.birthYear?.toString() ?? '';
    height.text = m.heightCm == null ? '' : formatForDisplay(m.heightCm!);
    weight.text = m.weightKg == null ? '' : formatForDisplay(m.weightKg!);
    bodyFat.text = m.bodyFatPct == null ? '' : formatForDisplay(m.bodyFatPct!);
    sex = m.sex?.json;
    direction = directionForGoal(m.goal?.json);
    if (s != null) {
      activity = s.activityLevel.json;
      direction = s.direction.json ?? direction;
      ratePct = s.ratePctBwPerWeek;
      targetWeight.text = s.targetWeightKg == null
          ? ''
          : formatForDisplay(s.targetWeightKg!);
      sexReference = s.sexReference?.json ?? 'average';
      pregnancy = s.pregnantOrBreastfeeding ? 'yes' : 'no';
      numbersDisplay = s.numbersDisplay.json ?? 'show';
    }
    notifyListeners();
  }

  @override
  void dispose() {
    birthYear.dispose();
    height.dispose();
    weight.dispose();
    bodyFat.dispose();
    targetWeight.dispose();
    super.dispose();
  }

  bool get _usesReference => sex == null || sex == 'other';

  int? get birthYearValue => int.tryParse(birthYear.text.trim());
  num? get heightValue => parseNumber(height.text).value;
  num? get weightValue => parseNumber(weight.text).value;
  num? get bodyFatValue => parseNumber(bodyFat.text).value;
  num? get targetWeightValue => parseNumber(targetWeight.text).value;

  /// A typed number that is not a plain decimal.
  bool get hasUnreadableNumber => [
    height.text,
    weight.text,
    bodyFat.text,
    targetWeight.text,
  ].any((t) => !parseNumber(t).ok);

  BodyDataIn toBody() => BodyDataIn(
    birthYear: birthYearValue,
    sex: sex == null ? null : BodyDataInSex.fromJson(sex!),
    heightCm: heightValue,
    weightKg: weightValue,
    bodyFatPct: bodyFatValue,
  );

  String? get _reference => _usesReference ? sexReference : null;
  num? get _rate => direction == 'maintain' ? null : ratePct;

  TargetsPreviewIn toPreview() => TargetsPreviewIn(
    direction: TargetsPreviewInDirection.fromJson(direction),
    activityLevel: TargetsPreviewInActivityLevel.fromJson(
      activity ?? 'sedentary',
    ),
    pregnantOrBreastfeeding: pregnancy != 'no',
    ratePctBwPerWeek: _rate,
    targetWeightKg: targetWeightValue,
    sexReference: _reference == null
        ? null
        : TargetsPreviewInSexReference.fromJson(_reference!),
    numbersDisplay: TargetsPreviewInNumbersDisplay.fromJson(numbersDisplay),
    body: toBody(),
  );

  GoalSettingsIn toSettings() => GoalSettingsIn(
    direction: GoalSettingsInDirection.fromJson(direction),
    activityLevel: GoalSettingsInActivityLevel.fromJson(
      activity ?? 'sedentary',
    ),
    pregnantOrBreastfeeding: pregnancy != 'no',
    ratePctBwPerWeek: _rate,
    targetWeightKg: targetWeightValue,
    sexReference: _reference == null
        ? null
        : GoalSettingsInSexReference.fromJson(_reference!),
    numbersDisplay: GoalSettingsInNumbersDisplay.fromJson(numbersDisplay),
    summaryView: stored == null
        ? GoalSettingsInSummaryView.remaining
        : GoalSettingsInSummaryView.fromJson(
            stored!.summaryView.json ?? 'remaining',
          ),
  );

  /// The member write for the body answers. Blank body fat clears a stored
  /// value (`clear_body_fat_pct`) and is otherwise left out; a value equal
  /// to the stored one is not re-sent.
  MemberDraft toMemberDraft(MemberOut primary) {
    final fat = bodyFatValue;
    final storedFat = primary.bodyFatPct;
    return MemberDraft.fromMember(primary).withBody(
      birthYear: birthYearValue ?? primary.birthYear,
      sex: sex,
      heightCm: heightValue,
      weightKg: weightValue,
      bodyFatPct: fat != null && fat != storedFat ? fat : null,
      clearBodyFat: fat == null && storedFat != null,
    );
  }
}
