import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../core/config/app_config.dart';
import '../../core/l10n/app_localizations.dart';
import '../../core/observability/analytics.dart';
import '../../core/theme/sn_colors.dart';
import '../../core/theme/tokens.g.dart';
import '../../features/meals/presentation/log_meal_sheet.dart';
import '../widgets/buttons.dart';
import '../widgets/off_attribution.dart';
import 'share_text.dart';

/// Opens the Android share sheet with [text]; overridden in tests.
final shareLauncherProvider = Provider<Future<void> Function(String text)>(
  (ref) => (text) async {
    await SharePlus.instance.share(ShareParams(text: text));
  },
);

/// The share URL for this locale (`SITE_URL`, then `/<locale>[/p/<barcode>]`).
String shareUrlFor(WidgetRef ref, String locale, {String? barcode}) =>
    shareUrl(ref.read(appConfigProvider).siteUrl, locale, barcode: barcode);

/// Share a scan result. The user picks which members' results go in (all
/// by default: a first name and a status word only, never a condition, an
/// allergen, a reason or a number).
Future<void> showResultShareSheet(
  BuildContext context, {
  required AnalyzeOut out,
  required String productName,
  required String url,
}) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) =>
      ShareSheet.result(out: out, productName: productName, url: url),
);

/// Share the family's week: counts only.
Future<void> showWeeklyShareSheet(
  BuildContext context, {
  required int scans,
  required int logged,
  required String url,
}) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  builder: (_) => ShareSheet.weekly(scans: scans, logged: logged, url: url),
);

class ShareSheet extends ConsumerStatefulWidget {
  const ShareSheet.result({
    super.key,
    required AnalyzeOut this.out,
    required String this.productName,
    required this.url,
  }) : scans = null,
       logged = null;

  const ShareSheet.weekly({
    super.key,
    required int this.scans,
    required int this.logged,
    required this.url,
  }) : out = null,
       productName = null;

  final AnalyzeOut? out;
  final String? productName;
  final int? scans;
  final int? logged;
  final String url;

  static const previewKey = Key('share-preview');
  static const shareKey = Key('share-send');

  @override
  ConsumerState<ShareSheet> createState() => _ShareSheetState();
}

class _ShareSheetState extends ConsumerState<ShareSheet> {
  late final Set<String> _picked = {
    for (final v in widget.out?.verdicts ?? const <VerdictOut>[]) v.memberId,
  };

  String? _text(AppLocalizations l10n) {
    final out = widget.out;
    if (out == null) {
      return shareWeeklyText(l10n, widget.scans!, widget.logged!, widget.url);
    }
    if (_picked.isEmpty) return null;
    return shareResultText(
      l10n,
      out,
      widget.productName!,
      widget.url,
      memberIds: _picked,
    );
  }

  Future<void> _share(String text) async {
    // Event name only: never the text, product or members.
    await ref
        .read(analyticsProvider)
        .track(widget.out == null ? 'share_weekly' : 'share_result');
    await ref.read(shareLauncherProvider)(text);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final text = _text(l10n);
    final out = widget.out;
    return Padding(
      padding: EdgeInsets.only(
        left: SnTokens.space4,
        right: SnTokens.space4,
        bottom: MediaQuery.viewInsetsOf(context).bottom + SnTokens.space4,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              out == null ? l10n.shareWeeklyButton : l10n.shareButton,
              style: theme.textTheme.titleLarge,
            ),
            const SizedBox(height: SnTokens.space3),
            if (out != null)
              for (final v in out.verdicts)
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  value: _picked.contains(v.memberId),
                  title: Text(memberLabel(l10n, v)),
                  onChanged: (on) => setState(() {
                    if (on ?? false) {
                      _picked.add(v.memberId);
                    } else {
                      _picked.remove(v.memberId);
                    }
                  }),
                ),
            if (text != null)
              Container(
                key: ShareSheet.previewKey,
                padding: const EdgeInsets.all(SnTokens.space3),
                decoration: BoxDecoration(
                  color: c.muted,
                  borderRadius: BorderRadius.circular(SnTokens.radiusMd),
                ),
                child: Text(text, style: theme.textTheme.bodyMedium),
              ),
            const SizedBox(height: SnTokens.space3),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.lock_outline_rounded,
                  size: SnTokens.fontSizeMd,
                  color: c.textSecondary,
                ),
                const SizedBox(width: SnTokens.space2),
                Expanded(
                  child: Text(
                    l10n.sharePrivacyNote,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: c.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: SnTokens.space4),
            PrimaryButton(
              buttonKey: ShareSheet.shareKey,
              label: l10n.shareButton,
              icon: Icons.share_rounded,
              onPressed: text == null ? null : () => _share(text),
            ),
            const SizedBox(height: SnTokens.space2),
            SecondaryButton(
              label: l10n.shareWhatsapp,
              icon: Icons.chat_rounded,
              onPressed: text == null
                  ? null
                  : () async {
                      await ref
                          .read(analyticsProvider)
                          .track(out == null ? 'share_weekly' : 'share_result');
                      await ref.read(openExternalUrlProvider)(
                        Uri.parse(
                          'https://wa.me/?text=${Uri.encodeComponent(text)}',
                        ),
                      );
                    },
            ),
            TextButton.icon(
              icon: const Icon(Icons.link_rounded),
              label: Text(l10n.shareCopyLink),
              onPressed: () async {
                final messenger = ScaffoldMessenger.of(context);
                await Clipboard.setData(ClipboardData(text: widget.url));
                messenger.showSnackBar(
                  SnackBar(content: Text(l10n.shareCopied)),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
