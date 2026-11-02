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
