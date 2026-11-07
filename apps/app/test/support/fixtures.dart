import 'dart:convert';
import 'dart:io';

import 'package:smartnutri_api/src/export.dart';

/// Shared fixtures live in `packages/test-fixtures`; `flutter test` runs from
/// the package root (`apps/app`). They are read from disk in tests only and are
/// never bundled into the app.
const _fixturesRoot = '../../packages/test-fixtures';

Map<String, Object?> _readJson(String relative) =>
    jsonDecode(File('$_fixturesRoot/$relative').readAsStringSync())
        as Map<String, Object?>;

/// Raw golden `POST /v1/analyze` body for [product] (a deep copy).
Map<String, Object?> analyzeJson(String product) =>
    _readJson('responses/analyze/$product.json');

AnalyzeOut analyzeFixture(String product) =>
    AnalyzeOut.fromJson(analyzeJson(product));

/// Fixture product names, sorted.
List<String> fixtureProducts() {
  final dir = Directory('$_fixturesRoot/responses/analyze');
  final names =
      dir
          .listSync()
          .whereType<File>()
          .where((f) => f.path.endsWith('.json'))
          .map((f) => f.uri.pathSegments.last.replaceAll('.json', ''))
          .toList()
        ..sort();
  return names;
}

/// member UUID -> member fixture name, from `responses/index.json`.
Map<String, String> memberNamesById() {
  final members = (_readJson('responses/index.json')['members'] as Map)
      .cast<String, String>();
  return {for (final e in members.entries) e.value: e.key};
}

class FixtureCase {
  FixtureCase(this.product, this.member, this.verdict);
  final String product;
  final String member;
  final VerdictOut verdict;
}

/// One case per verdict in every golden analyze response.
List<FixtureCase> sharedFixtureCases() {
  final names = memberNamesById();
  return [
    for (final product in fixtureProducts())
      for (final v in analyzeFixture(product).verdicts)
        FixtureCase(product, names[v.memberId]!, v),
  ];
}

VerdictOut fixtureVerdict(String product, String member) => sharedFixtureCases()
    .firstWhere((c) => c.product == product && c.member == member)
    .verdict;

/// `expected/<product>.<member>.json`: the engine's status and reason codes.
Map<String, Object?> expectedFixture(String product, String member) =>
    _readJson('expected/$product.$member.json');

/// `drafts/<case>.json`: a `ProductDraft` exactly as the API returns it (R21).
Map<String, Object?> draftJson(String name) => _readJson('drafts/$name.json');

ProductDraft draftFixture(String name) =>
    ProductDraft.fromJson(draftJson(name));

/// `drafts/expected.json` (`{"format_version": 1, "cases": {...}}`).
Map<String, Object?> draftExpectationsFile() =>
    _readJson('drafts/expected.json');

/// Case names that have a `drafts/<case>.json` file, sorted.
List<String> draftFixtureNames() =>
    Directory('$_fixturesRoot/drafts')
        .listSync()
        .whereType<File>()
        .map((f) => f.uri.pathSegments.last)
        .where((n) => n.endsWith('.json') && n != 'expected.json')
        .map((n) => n.replaceAll('.json', ''))
        .toList()
      ..sort();

/// Golden `GET /v1/methodology` body (English).
Methodology methodologyFixture() =>
    Methodology.fromJson(_readJson('responses/methodology.json'));

/// Golden `POST /v1/voice/ask` body ([name] is e.g. `answer_avoid`).
VoiceAnswer voiceAnswerFixture(String name) =>
    VoiceAnswer.fromJson(_readJson('responses/voice/$name.json'));

/// Golden `GET /v1/targets` body (`targets/expected/<stem>.json`).
Map<String, Object?> targetsJson(String stem) =>
    _readJson('targets/expected/$stem.json');

TargetsOut targetsFixture(String stem) =>
    TargetsOut.fromJson(targetsJson(stem));

/// Stems that have an `expected/<stem>.json` file with a `status` (no
/// `error` files), sorted.
List<String> targetsFixtureStems() =>
    Directory('$_fixturesRoot/targets/expected')
        .listSync()
        .whereType<File>()
        .map((f) => f.uri.pathSegments.last)
        .where((n) => n.endsWith('.json'))
        .map((n) => n.replaceAll('.json', ''))
        .toList()
      ..sort();

/// `targets/direction_defaults.json`.
Map<String, String> directionDefaultsFixture() =>
    (_readJson('targets/direction_defaults.json')).cast<String, String>();

/// Golden `GET /v1/diary/day` or `/week` body (`diary/expected/<stem>.json`).
Map<String, Object?> diaryJson(String stem) =>
    _readJson('diary/expected/$stem.json');

DiaryDayOut diaryFixture(String stem) => DiaryDayOut.fromJson(diaryJson(stem));

DiaryWeekOut diaryWeekFixture(String stem) =>
    DiaryWeekOut.fromJson(diaryJson(stem));

/// Golden `GET /v1/weights/trend` body (`weights/expected/<stem>.json`).
Map<String, Object?> weightTrendJson(String stem) =>
    _readJson('weights/expected/$stem.json');

/// The golden trend; the fixture has no member or range, so they are filled.
WeightTrendOut weightTrendFixture(String stem, {int days = 90}) {
  final json = weightTrendJson(stem);
  final points = (json['points'] as List).cast<Map<String, Object?>>();
  return WeightTrendOut.fromJson({
    'member_id': 'p1',
    'days': days,
    'from': points.isEmpty ? '2026-01-01' : points.first['date'],
    'to': points.isEmpty ? '2026-01-01' : points.last['date'],
    ...json,
  });
}

/// `weights/inputs/<stem>.json`'s weigh-ins as the list the API would give.
WeightsOut weightsListFixture(String stem) {
  final input = _readJson('weights/inputs/$stem.json');
  final hidden = weightTrendJson(stem)['numbers_hidden'] == true;
  return WeightsOut(
    numbersHidden: hidden,
    items: [
      for (final w in (input['weigh_ins'] as List).cast<Map<String, Object?>>())
        WeightOut(
          clientId: null,
          date: DateTime.parse(w['date']! as String),
          measuredAt: DateTime.parse('${w['date']}T07:00:00Z'),
          numbersHidden: hidden,
          source: 'manual',
          weightKg: hidden ? null : w['weight_kg'] as num,
        ),
    ],
  );
}
