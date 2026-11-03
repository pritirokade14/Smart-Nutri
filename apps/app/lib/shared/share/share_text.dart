/// Privacy-safe share texts (F17), byte-identical to the web client for the
/// same locale (`packages/test-fixtures/share/*.json` enforce it).
///
/// Built only from `share.*` and `verdict.status.*` strings: the product
/// name, its grade, each picked member's first name (or relation) and their
/// status word, and counts. Never conditions, allergens, reason codes or
/// nutrient totals.
library;

// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../core/l10n/app_localizations.dart';
import '../../features/analysis/domain/report.dart';

/// `share.relation.<relation>`; anything unknown is "Family member".
String shareRelation(AppLocalizations l, String? relation) =>
    switch (relation) {
      'self' => l.shareRelationSelf,
      'child' => l.shareRelationChild,
      'parent' => l.shareRelationParent,
      'spouse' => l.shareRelationSpouse,
      _ => l.shareRelationOther,
    };

/// `verdict.status.<status>`; anything unrecognised is "Label unclear".
String _status(AppLocalizations l, VerdictOutStatus status) => switch (status) {
  VerdictOutStatus.ok => l.verdictStatusOk,
  VerdictOutStatus.caution => l.verdictStatusCaution,
  VerdictOutStatus.avoid => l.verdictStatusAvoid,
  _ => l.verdictStatusUnknown,
};

/// The first whitespace-separated word of the member's name, or the
/// relation when the name is blank.
String shareWho(AppLocalizations l, VerdictOut v) {
  final words = v.memberName.trim().split(RegExp(r'\s+'));
  final first = words.isEmpty ? '' : words.first;
  return first.isEmpty ? shareRelation(l, v.relation.json) : first;
}

/// The result share text. [memberIds] limits it to the members the user
/// picked (default: all), in API order.
String shareResultText(
  AppLocalizations l,
  AnalyzeOut r,
  String productName,
  String url, {
  Set<String>? memberIds,
}) {
  final members = [
    for (final v in r.verdicts)
      if (memberIds == null || memberIds.contains(v.memberId))
        l.shareResultMember(_status(l, v.status), shareWho(l, v)),
  ].join(', ');
  final grade = nutriscoreGrade(r.report);
  return grade == null
      ? l.shareResultUngraded(members, productName, url)
      : l.shareResultText(grade, members, productName, url);
}

/// The weekly family share text: counts only, as plain Latin digits.
String shareWeeklyText(AppLocalizations l, int scans, int logged, String url) =>
    l.shareWeekly(logged.toString(), scans.toString(), url);

/// The public product page for a barcode (`/<locale>/p/<barcode>`), else the
/// site's home page for [locale].
String shareUrl(String siteUrl, String locale, {String? barcode}) {
  final base = siteUrl.endsWith('/')
      ? siteUrl.substring(0, siteUrl.length - 1)
      : siteUrl;
  return barcode == null || barcode.isEmpty
      ? '$base/$locale'
      : '$base/$locale/p/$barcode';
}
