import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/l10n/app_localizations.dart';
import '../../../core/theme/sn_colors.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/disclaimer_footer.dart';
import '../../../shared/widgets/states.dart';

bool isValidEmail(String v) => v.trim().contains('@');
bool isValidPhone(String v) => RegExp(r'^\+\d{8,15}$').hasMatch(v.trim());
bool isValidCode(String v) => RegExp(r'^\d{6}$').hasMatch(v.trim());

/// Two-step "send code, then verify" form shared by email and phone sign-in.
class OtpForm extends StatefulWidget {
  const OtpForm({
    super.key,
    required this.identifierLabel,
    required this.keyboardType,
    required this.isValidIdentifier,
    required this.onSend,
    required this.onVerify,
  });

  final String Function(AppLocalizations l10n) identifierLabel;
  final TextInputType keyboardType;
  final bool Function(String identifier) isValidIdentifier;
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
  void initState() {
    super.initState();
    _id.addListener(_refresh);
    _code.addListener(_refresh);
  }

  void _refresh() => setState(() {});

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

  void _change() {
    _code.clear();
    setState(() {
      _sent = false;
      _failed = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    final idOk = widget.isValidIdentifier(_id.text);
    final codeOk = isValidCode(_code.text);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.authTitle)),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) => SingleChildScrollView(
            padding: const EdgeInsets.all(SnTokens.space5),
            child: ConstrainedBox(
              constraints: BoxConstraints(
                minHeight: constraints.maxHeight - SnTokens.space5 * 2,
              ),
              child: IntrinsicHeight(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      l10n.appName,
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: c.brandStrong,
                      ),
                    ),
                    const SizedBox(height: SnTokens.space1),
                    Text(
                      l10n.authTagline,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: c.textSecondary,
                      ),
                    ),
                    const SizedBox(height: SnTokens.space5),
                    TextField(
                      controller: _id,
                      keyboardType: widget.keyboardType,
                      enabled: !_sent,
                      decoration: InputDecoration(
                        labelText: widget.identifierLabel(l10n),
                      ),
                    ),
                    const SizedBox(height: SnTokens.space4),
                    if (_sent) ...[
                      TextField(
                        controller: _code,
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                          LengthLimitingTextInputFormatter(6),
                        ],
                        decoration: InputDecoration(
                          labelText: l10n.authCodeLabel,
                        ),
                      ),
                      const SizedBox(height: SnTokens.space4),
                      PrimaryButton(
                        label: l10n.authVerify,
                        onPressed: _busy || !codeOk
                            ? null
                            : () => _run(
                                () => widget.onVerify(
                                  _id.text.trim(),
                                  _code.text.trim(),
                                ),
                              ),
                      ),
                      const SizedBox(height: SnTokens.space2),
                      TextButton(
                        onPressed: _busy ? null : _change,
                        child: Text(l10n.authChange),
                      ),
                    ] else
                      PrimaryButton(
                        label: l10n.authSendCode,
                        onPressed: _busy || !idOk
                            ? null
                            : () => _run(
                                () => widget.onSend(_id.text.trim()),
                                sends: true,
                              ),
                      ),
                    if (_failed) ...[
                      const SizedBox(height: SnTokens.space4),
                      InlineErrorBanner(message: l10n.authError),
                    ],
                    const Spacer(),
                    const SizedBox(height: SnTokens.space4),
                    const DisclaimerFooter(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
