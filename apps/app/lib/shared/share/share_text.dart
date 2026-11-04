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

/// Ruling SH1: `share.link` is appended only when there is a [url] (a
/// configured `SITE_URL`); otherwise the text carries no link at all.
String _withLink(AppLocalizations l, String body, String? url) =>
    url == null || url.isEmpty ? body : '$body ${l.shareLink(url)}';

/// The result share text: the product and its grade, plus the members the
/// user ticked ([memberIds], none by default: ruling SH1), in API order.
/// [url] is null when no `SITE_URL` is configured.
String shareResultText(
  AppLocalizations l,
  AnalyzeOut r,
  String productName,
  String? url, {
  Set<String> memberIds = const {},
}) {
  final members = [
    for (final v in r.verdicts)
      if (memberIds.contains(v.memberId))
        l.shareResultMember(_status(l, v.status), shareWho(l, v)),
  ].join(', ');
  final grade = nutriscoreGrade(r.report);
  final String body;
  if (members.isEmpty) {
    body = grade == null
        ? l.shareResultProductOnlyUngraded(productName)
        : l.shareResultProductOnly(grade, productName);
  } else {
    body = grade == null
        ? l.shareResultUngraded(members, productName)
        : l.shareResultText(grade, members, productName);
  }
  return _withLink(l, body, url);
}

/// The weekly family share text: counts only, as plain Latin digits.
String shareWeeklyText(
  AppLocalizations l,
  int scans,
  int logged,
  String? url,
) => _withLink(l, l.shareWeekly(logged.toString(), scans.toString()), url);

/// The public product page for a barcode (`/<locale>/p/<barcode>`), else the
/// site's home page for [locale]; null when [siteUrl] (`SITE_URL`) is empty
/// (ruling SH1: never a hard-coded domain).
String? shareUrl(String siteUrl, String locale, {String? barcode}) {
  var base = siteUrl.trim();
  if (base.isEmpty) return null;
  while (base.endsWith('/')) {
    base = base.substring(0, base.length - 1);
  }
  return barcode == null || barcode.isEmpty
      ? '$base/$locale'
      : '$base/$locale/p/$barcode';
}
