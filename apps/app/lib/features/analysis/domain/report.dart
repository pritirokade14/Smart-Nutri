/// Read-only accessors for the `report` object of `AnalyzeOut` (a free-form
/// map in the contract). Nothing here computes or changes a result.
library;

const _grades = {'A', 'B', 'C', 'D', 'E'};

Map<String, Object?> _map(Object? v) =>
    v is Map ? v.cast<String, Object?>() : const {};

/// `report.nutriscore.grade` (A–E) as calculated by the API, or null when the
/// API had too little label data to calculate one.
String? nutriscoreGrade(Object? report) {
  final grade = _map(_map(report)['nutriscore'])['grade'];
  return grade is String && _grades.contains(grade) ? grade : null;
}

/// `report.high_in`: codes (`sugar`, `fat`, `sat_fat`, `salt`) in API order.
List<String> highInCodes(Object? report) {
  final v = _map(report)['high_in'];
  return v is List ? v.whereType<String>().toList() : const [];
}

/// One front-of-pack claim check from `report.claims`, as the API sent it.
typedef ClaimCheck = ({
  String claim,
  String verdict,
  String reasonCode,
  Map<String, Object?> params,
});

const _claimVerdicts = {'supported', 'contradicted', 'unverifiable'};

/// `report.claims` in API order. Entries that are malformed or carry a claim
/// verdict this build does not know are skipped (as on the web).
List<ClaimCheck> claimChecks(Object? report) {
  final v = _map(report)['claims'];
  if (v is! List) return const [];
  return [
    for (final e in v)
      if (e is Map)
        if ((e['claim'], e['verdict'], e['reason_code']) case (
          final String claim,
          final String verdict,
          final String reasonCode,
        ) when _claimVerdicts.contains(verdict))
          (
            claim: claim,
            verdict: verdict,
            reasonCode: reasonCode,
            params: _map(e['params']),
          ),
  ];
}

/// `report.nutriscore.reason`, e.g. `not_scored_supplement` (no grade is
/// calculated for supplements), or null.
String? nutriscoreReason(Object? report) {
  final reason = _map(_map(report)['nutriscore'])['reason'];
  return reason is String ? reason : null;
}

/// `report.protein` as the API calculated it. A missing value is null (never
/// 0): per serving needs a serving size, per 100 kcal needs the energy.
typedef ProteinFacts = ({num? perServing, num? per100g, num? per100kcal});

ProteinFacts? proteinFacts(Object? report) {
  final raw = _map(report)['protein'];
  if (raw is! Map) return null;
  final p = _map(raw);
  num? n(String k) => p[k] is num ? p[k]! as num : null;
  return (
    perServing: n('per_serving'),
    per100g: n('per_100g'),
    per100kcal: n('per_100kcal'),
  );
}

List<String> _strings(Object? report, String key) {
  final v = _map(report)[key];
  return v is List ? v.whereType<String>().toList() : const [];
}

/// `report.sweeteners`: information from the ingredients, not a warning.
List<String> sweetenersIn(Object? report) => _strings(report, 'sweeteners');

/// `report.caffeine`: information from the ingredients, not a warning.
List<String> caffeineIn(Object? report) => _strings(report, 'caffeine');
