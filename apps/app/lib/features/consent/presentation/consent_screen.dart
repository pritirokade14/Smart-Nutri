import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/states.dart';
import '../../auth/data/auth_repository.dart';
import '../../members/data/members_repository.dart';
import '../../members/presentation/members_providers.dart';
import '../domain/consent_error.dart';
import 'policy_links.dart';

/// Asks the user to agree to [purposes] (F11).
///
/// - **Gate** (`/terms`, [gate] true): shown after sign-in until the current
///   terms are agreed. There is no way back; the alternative is signing out.
///   Once agreed, the router moves on by itself.
/// - **Pushed** (`/consent?purposes=`): opened by a 403 `consent_required`
///   (e.g. `ai_processing` for voice) or to review updated texts. Pops true
///   once agreed, false on "Not now".
class ConsentScreen extends ConsumerStatefulWidget {
  ConsentScreen({super.key, required List<String> purposes, this.gate = false})
    : purposes = [
        for (final p in knownConsentPurposes)
          if (purposes.contains(p)) p,
      ];

  final List<String> purposes;
  final bool gate;

  static const agreeKey = Key('consent-screen-agree');
  static const declineKey = Key('consent-screen-decline');

  /// Parses `?purposes=a,b`.
  static List<String> parsePurposes(String? raw) =>
      (raw ?? '').split(',').map((p) => p.trim()).toList();

  @override
  ConsumerState<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends ConsumerState<ConsentScreen> {
  bool _busy = false;
  String? _error;

  Future<void> _agree() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(consentStateProvider.notifier).record({
        for (final p in widget.purposes) p: true,
      });
      if (!mounted) return;
      if (widget.gate) {
        setState(() => _busy = false); // the router leaves this screen
      } else {
        Navigator.of(context).pop(true);
      }
    } on MembersFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(AppLocalizations.of(context), e.code);
      });
    }
  }

  void _decline() {
    if (widget.gate) {
      ref.read(authRepositoryProvider).signOut();
    } else {
      Navigator.of(context).pop(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final states = ref.watch(consentStateProvider);
    return PopScope(
      canPop: !widget.gate,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.consentScreenTitle),
          automaticallyImplyLeading: !widget.gate,
        ),
        body: SafeArea(
          child: states.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(SnTokens.space4),
              child: LoadingSkeleton(lines: 4),
            ),
            error: (e, _) => Center(
              child: ErrorState(
                message: localizedErrorCode(
                  l10n,
                  e is MembersFailure ? e.code : null,
                ),
                onRetry: () => ref.invalidate(consentStateProvider),
                actions: [
                  TextButton(
                    key: ConsentScreen.declineKey,
                    onPressed: _decline,
                    child: Text(
                      widget.gate ? l10n.authSignOut : l10n.consentDecline,
                    ),
                  ),
                ],
              ),
            ),
            data: (list) => _body(context, l10n, list),
          ),
        ),
      ),
    );
  }

  Widget _body(
    BuildContext context,
    AppLocalizations l10n,
    List<ConsentState> states,
  ) {
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    return ListView(
      padding: const EdgeInsets.all(SnTokens.space4),
      children: [
        Text(l10n.consentScreenIntro, style: theme.textTheme.bodyLarge),
        const SizedBox(height: SnTokens.space4),
        for (final purpose in widget.purposes)
          Card(
            margin: const EdgeInsets.only(bottom: SnTokens.space3),
            child: Padding(
              padding: const EdgeInsets.all(SnTokens.space4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    consentTitle(l10n, purpose),
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: SnTokens.space2),
                  Text(
                    consentBody(l10n, purpose),
                    style: theme.textTheme.bodyMedium,
                  ),
                  if (_needsUpdate(states, purpose)) ...[
                    const SizedBox(height: SnTokens.space2),
                    Text(
                      l10n.consentUpdateNote,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                  ],
                  if (purpose == consentPurposeTerms) ...[
                    const SizedBox(height: SnTokens.space2),
                    const PolicyLinks(),
                  ],
                ],
              ),
            ),
          ),
        if (_error case final message?) ...[
          InlineErrorBanner(message: message),
          const SizedBox(height: SnTokens.space3),
        ],
        const SizedBox(height: SnTokens.space2),
        PrimaryButton(
          buttonKey: ConsentScreen.agreeKey,
          label: l10n.consentAgree,
          busy: _busy,
          onPressed: widget.purposes.isEmpty ? null : _agree,
        ),
        const SizedBox(height: SnTokens.space2),
        TextButton(
          key: ConsentScreen.declineKey,
          onPressed: _busy ? null : _decline,
          child: Text(widget.gate ? l10n.authSignOut : l10n.consentDecline),
        ),
      ],
    );
  }

  static bool _needsUpdate(List<ConsentState> states, String purpose) =>
      states.any((s) => s.purpose == purpose && s.needsUpdate);
}

/// The consent's title, as in the profile and the sheets.
String consentTitle(AppLocalizations l10n, String purpose) => switch (purpose) {
  consentPurposeTerms => l10n.consentTermsTitle,
  consentPurposeHealthData => l10n.consentHealthDataTitle,
  _ => l10n.consentAiProcessingTitle,
};

/// What the user agrees to.
String consentBody(AppLocalizations l10n, String purpose) => switch (purpose) {
  consentPurposeTerms => l10n.consentTermsBody,
  consentPurposeHealthData => l10n.consentHealthDataBody,
  _ => l10n.consentAiProcessingBody,
};
