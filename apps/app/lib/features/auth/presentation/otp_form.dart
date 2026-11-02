import 'package:flutter/material.dart';

import '../../../core/l10n/app_localizations.dart';

/// Two-step "send code, then verify" form shared by email and phone sign-in.
class OtpForm extends StatefulWidget {
  const OtpForm({
    super.key,
    required this.identifierLabel,
    required this.keyboardType,
    required this.onSend,
    required this.onVerify,
  });

  final String Function(AppLocalizations l10n) identifierLabel;
  final TextInputType keyboardType;
  final Future<void> Function(String identifier) onSend;
  final Future<void> Function(String identifier, String code) onVerify;

  @override
  State<OtpForm> createState() => _OtpFormState();
}

class _OtpFormState extends State<OtpForm> {
  final _id = TextEditingController();
  final _code = TextEditingController();
  bool _sent = false;
  bool _busy = false;
  bool _failed = false;

  @override
  void dispose() {
    _id.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _run(
    Future<void> Function() action, {
    bool sends = false,
  }) async {
    setState(() {
      _busy = true;
      _failed = false;
    });
    try {
      await action();
      if (mounted && sends) setState(() => _sent = true);
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.authTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _id,
              keyboardType: widget.keyboardType,
              enabled: !_sent,
              decoration: InputDecoration(
                labelText: widget.identifierLabel(l10n),
              ),
            ),
            const SizedBox(height: 16),
            if (_sent) ...[
              TextField(
                controller: _code,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: l10n.authCodeLabel),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _busy
                    ? null
                    : () => _run(
                        () =>
                            widget.onVerify(_id.text.trim(), _code.text.trim()),
                      ),
                child: Text(l10n.authVerify),
              ),
            ] else
              FilledButton(
                onPressed: _busy
                    ? null
                    : () => _run(
                        () => widget.onSend(_id.text.trim()),
                        sends: true,
                      ),
                child: Text(l10n.authSendCode),
              ),
            if (_failed) ...[
              const SizedBox(height: 16),
              Text(
                l10n.errorInternalError,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const Spacer(),
            Text(l10n.commonDisclaimer, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
