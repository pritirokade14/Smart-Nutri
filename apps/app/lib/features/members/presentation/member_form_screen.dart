import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
import '../../scan/domain/number_text.dart';
import '../data/members_repository.dart';
import '../domain/member.dart';
import 'consent_sheet.dart';
import 'member_labels.dart';
import 'members_providers.dart';

/// Add a family member ([memberId] null) or edit one. Saving sends the whole
/// form; health fields need the `health_data` consent, asked for in the
/// [ConsentSheet] before the save (and again on a 403 `consent_required`).
class MemberFormScreen extends ConsumerWidget {
  const MemberFormScreen({super.key, this.memberId});

  final String? memberId;

  static const nameKey = Key('member-form-name');
  static const birthYearKey = Key('member-form-birth-year');
  static const heightKey = Key('member-form-height');
  static const weightKey = Key('member-form-weight');
  static const otherAllergenKey = Key('member-form-other-allergen');
  static const addAllergenKey = Key('member-form-add-allergen');
  static const saveKey = Key('member-form-save');
  static const removeKey = Key('member-form-remove');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final id = memberId;
    if (id == null) {
      return Scaffold(
        appBar: AppBar(title: Text(l10n.membersAdd)),
        body: const _MemberForm(member: null),
      );
    }
    final members = ref.watch(membersProvider);
    return members.when(
      loading: () => Scaffold(
        appBar: AppBar(title: Text(l10n.membersEdit)),
        body: const SingleChildScrollView(
          padding: EdgeInsets.all(SnTokens.space4),
          child: LoadingSkeleton(lines: 6),
        ),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: Text(l10n.membersEdit)),
        body: Center(
          child: ErrorState(
            message: localizedErrorCode(
              l10n,
              e is MembersFailure ? e.code : null,
            ),
            onRetry: () => ref.invalidate(membersProvider),
          ),
        ),
      ),
      data: (list) {
        final member = list.where((m) => m.id == id).firstOrNull;
        if (member == null) {
          return Scaffold(
            appBar: AppBar(title: Text(l10n.membersEdit)),
            body: Center(child: ErrorState(message: l10n.errorMemberNotFound)),
          );
        }
        return Scaffold(
          appBar: AppBar(
            title: Text(member.isPrimary ? l10n.membersYouBadge : member.name),
          ),
          body: _MemberForm(key: ValueKey(member.id), member: member),
        );
      },
    );
  }
}

class _MemberForm extends ConsumerStatefulWidget {
  const _MemberForm({super.key, required this.member});

  /// The stored member, or null for a new one.
  final MemberOut? member;

  @override
  ConsumerState<_MemberForm> createState() => _MemberFormState();
}

class _MemberFormState extends ConsumerState<_MemberForm> {
  final _formKey = GlobalKey<FormState>();
  late final MemberDraft _initial = widget.member == null
      ? const MemberDraft()
      : MemberDraft.fromMember(widget.member!);

  late final _name = TextEditingController(text: _initial.name);
  late final _birthYear = TextEditingController(
    text: _initial.birthYear?.toString() ?? '',
  );
  late final _height = TextEditingController(
    text: _initial.heightCm == null ? '' : formatForDisplay(_initial.heightCm!),
  );
  late final _weight = TextEditingController(
    text: _initial.weightKg == null ? '' : formatForDisplay(_initial.weightKg!),
  );
  final _other = TextEditingController();

  late String? _relation = _initial.relation;
  late String? _sex = _initial.sex;
  late String _diet = _initial.diet;
  late String? _goal = _initial.goal;
  late final List<String> _allergens = [..._initial.allergens];
  late final List<String> _conditions = [..._initial.conditions];
  late final List<String> _alerts = [..._initial.customAlerts];

  bool _submitted = false;
  bool _busy = false;
  String? _error;
  String? _otherError;

  bool get _isPrimary => widget.member?.isPrimary ?? false;

  @override
  void dispose() {
    _name.dispose();
    _birthYear.dispose();
    _height.dispose();
    _weight.dispose();
    _other.dispose();
    super.dispose();
  }

  MemberDraft _draft() => MemberDraft(
    name: _name.text.trim(),
    relation: _relation,
    birthYear: int.tryParse(_birthYear.text.trim()),
    sex: _sex,
    heightCm: parseNumber(_height.text).value,
    weightKg: parseNumber(_weight.text).value,
    diet: _diet,
    allergens: List.unmodifiable(_allergens),
    conditions: [
      for (final c in conditionKeys)
        if (_conditions.contains(c)) c,
    ],
    customAlerts: [
      for (final a in customAlertKeys)
        if (_alerts.contains(a)) a,
    ],
    goal: _goal,
  );

  /// The member's name for confirm dialogs.
  String _displayName(AppLocalizations l10n) {
    final name = _name.text.trim();
    if (name.isNotEmpty) return name;
    return _isPrimary ? l10n.membersYouBadge : relationLabel(l10n, _relation);
  }

  Future<void> _save() async {
    setState(() {
      _submitted = true;
      _error = null;
    });
    final valid = _formKey.currentState?.validate() ?? false;
    if (!valid || _relation == null) return;
    final draft = _draft();
    final consents = ref.read(consentStateProvider).value;
    // Ask first when we know consent is missing; if the states are not
    // loaded, the API's 403 opens the same sheet.
    if (writesHealthData(draft, stored: widget.member) &&
        consentGranted(consents, consentPurposeHealthData) == false) {
      if (!await showConsentSheet(context)) return;
    }
    await _submit(draft, consentRetry: true);
  }

  Future<void> _submit(MemberDraft draft, {required bool consentRetry}) async {
    if (!mounted) return;
    final l10n = AppLocalizations.of(context);
    setState(() => _busy = true);
    final notifier = ref.read(membersProvider.notifier);
    final id = widget.member?.id;
    try {
      if (id == null) {
        await notifier.create(draft);
      } else {
        await notifier.updateMember(id, draft);
      }
      if (!mounted) return;
      ScaffoldMessenger.maybeOf(
        context,
      )?.showSnackBar(SnackBar(content: Text(l10n.membersSaved)));
      final popped = await Navigator.of(context).maybePop();
      if (!popped && mounted) setState(() => _busy = false);
    } on MembersFailure catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      if (e.isConsentRequired && consentRetry) {
        if (await showConsentSheet(context)) {
          await _submit(draft, consentRetry: false);
        }
        return;
      }
      setState(() => _error = localizedErrorCode(l10n, e.code));
    }
  }

  Future<void> _remove() async {
    final l10n = AppLocalizations.of(context);
    final member = widget.member!;
    final ok = await _confirm(
      l10n.membersRemoveConfirm(_displayName(l10n)),
      l10n.membersRemove,
    );
    if (!ok || !mounted) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(membersProvider.notifier).remove(member.id);
      if (mounted) await Navigator.of(context).maybePop();
    } on MembersFailure catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = localizedErrorCode(l10n, e.code);
      });
    }
  }

  Future<bool> _confirm(String message, String action) async {
    final l10n = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.membersFormCancel),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(action),
          ),
        ],
      ),
    );
    return ok ?? false;
  }

  /// Removing an allergy always asks first: a removed allergy is no longer
  /// flagged on products.
  Future<void> _removeAllergen(String allergen) async {
    final l10n = AppLocalizations.of(context);
    final name = _displayName(l10n);
    final message = _allergens.length == 1
        ? l10n.membersFormClearAllergiesConfirm(name)
        : l10n.membersFormRemoveAllergyConfirm(
            allergenLabel(l10n, allergen),
            name,
          );
    if (await _confirm(message, l10n.membersRemove)) {
      setState(() => _allergens.remove(allergen));
    }
  }

  void _addAllergen(String value) {
    final l10n = AppLocalizations.of(context);
    if (_allergens.any((a) => a.toLowerCase() == value.toLowerCase())) return;
    if (_allergens.length >= maxAllergens) {
      setState(() => _otherError = l10n.membersFormAllergenLimit);
      return;
    }
    setState(() {
      _otherError = null;
      _allergens.add(value);
    });
  }

  void _addOther() {
    final l10n = AppLocalizations.of(context);
    final text = _other.text.trim();
    if (text.length < allergenMinLength || text.length > allergenMaxLength) {
      setState(() => _otherError = l10n.membersFormAllergenLength);
      return;
    }
    // Typing a listed allergy (its key or its label) picks the listed one.
    final folded = text.toLowerCase();
    final canonical = canonicalAllergens.where(
      (k) => k == folded || allergenLabel(l10n, k).toLowerCase() == folded,
    );
    _addAllergen(canonical.firstOrNull ?? text);
    if (_otherError == null) _other.clear();
  }

  String? _numberError(String text, ({int min, int max}) range) {
    final parsed = parseNumber(text);
    final v = parsed.value;
    if (!parsed.ok || (v != null && (v < range.min || v > range.max))) {
      return AppLocalizations.of(
        context,
      ).membersFormNumberRange('${range.max}', '${range.min}');
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final c = SnColors.of(context);
    // Load the consent states so a missing consent is asked for before save.
    ref.watch(consentStateProvider);
    final thisYear = DateTime.now().year;
    final custom = [
      for (final a in _allergens)
        if (!canonicalAllergens.contains(a)) a,
    ];

    Widget section(String title, {String? help}) => Padding(
      padding: const EdgeInsets.only(
        top: SnTokens.space5,
        bottom: SnTokens.space2,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: theme.textTheme.titleMedium),
          if (help != null)
            Text(
              help,
              style: theme.textTheme.bodySmall?.copyWith(
                color: c.textSecondary,
              ),
            ),
        ],
      ),
    );

    Widget choices(
      List<String> keys,
      String? selected,
      String Function(String) label,
      void Function(String?) onChanged, {
      bool optional = false,
    }) => Wrap(
      spacing: SnTokens.space2,
      runSpacing: SnTokens.space2,
      children: [
        for (final k in keys)
          ChoiceChip(
            label: Text(label(k)),
            selected: selected == k,
            onSelected: _busy
                ? null
                : (on) => setState(
                    () => onChanged(on ? k : (optional ? null : selected)),
                  ),
          ),
      ],
    );

    return Form(
      key: _formKey,
      autovalidateMode: _submitted
          ? AutovalidateMode.onUserInteraction
          : AutovalidateMode.disabled,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          SnTokens.space4,
          SnTokens.space3,
          SnTokens.space4,
          SnTokens.space6,
        ),
        children: [
          TextFormField(
            key: MemberFormScreen.nameKey,
            controller: _name,
            enabled: !_busy,
            maxLength: 40,
            textCapitalization: TextCapitalization.words,
            decoration: InputDecoration(labelText: l10n.membersFormName),
            validator: (v) => (v == null || v.trim().isEmpty)
                ? l10n.membersFormNameRequired
                : null,
          ),
          section(l10n.membersFormRelation),
          if (_isPrimary)
            Text(l10n.membersRelationSelf, style: theme.textTheme.bodyLarge)
          else ...[
            choices(
              newRelationKeys,
              _relation,
              (k) => relationLabel(l10n, k),
              (v) => _relation = v,
            ),
            if (_submitted && _relation == null)
              Padding(
                padding: const EdgeInsets.only(top: SnTokens.space1),
                child: Text(
                  l10n.confirmChooseRequired,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.error,
                  ),
                ),
              ),
          ],
          const SizedBox(height: SnTokens.space4),
          TextFormField(
            key: MemberFormScreen.birthYearKey,
            controller: _birthYear,
            enabled: !_busy,
            keyboardType: TextInputType.number,
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(4),
            ],
            decoration: InputDecoration(
              labelText: l10n.membersFormBirthYear,
              helperText: l10n.membersFormBirthYearHelp,
              helperMaxLines: 2,
            ),
            validator: (v) {
              final year = int.tryParse(v?.trim() ?? '');
              return year == null || year < birthYearMin || year > thisYear
                  ? l10n.membersFormBirthYearInvalid('$thisYear')
                  : null;
            },
          ),
          section(l10n.membersFormSex),
          choices(
            sexKeys,
            _sex,
            (k) => sexLabel(l10n, k),
            (v) => _sex = v,
            optional: true,
          ),
          section(l10n.membersFormDiet),
          choices(
            dietKeys,
            _diet,
            (k) => dietLabel(l10n, k),
            (v) => _diet = v ?? _diet,
          ),
          Padding(
            padding: const EdgeInsets.only(top: SnTokens.space5),
            child: Container(
              padding: const EdgeInsets.all(SnTokens.space3),
              decoration: BoxDecoration(
                color: c.brandSoft,
                borderRadius: BorderRadius.circular(SnTokens.radiusMd),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.shield_outlined, color: c.brandStrong),
                  const SizedBox(width: SnTokens.space2),
                  Expanded(
                    child: Text(
                      l10n.membersFormHealthFieldsNote,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: c.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          section(
            l10n.membersFormAllergens,
            help: l10n.membersFormAllergensHelp,
          ),
          Wrap(
            spacing: SnTokens.space2,
            runSpacing: SnTokens.space2,
            children: [
              for (final k in canonicalAllergens)
                FilterChip(
                  label: Text(allergenLabel(l10n, k)),
                  selected: _allergens.contains(k),
                  onSelected: _busy
                      ? null
                      : (on) => on ? _addAllergen(k) : _removeAllergen(k),
                ),
              for (final a in custom)
                InputChip(
                  label: Text(a),
                  selected: true,
                  onPressed: null,
                  onDeleted: _busy ? null : () => _removeAllergen(a),
                ),
            ],
          ),
          const SizedBox(height: SnTokens.space3),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextField(
                  key: MemberFormScreen.otherAllergenKey,
                  controller: _other,
                  enabled: !_busy,
                  maxLength: allergenMaxLength,
                  decoration: InputDecoration(
                    labelText: l10n.membersFormAllergenOther,
                    errorText: _otherError,
                    counterText: '',
                  ),
                  onSubmitted: (_) => _addOther(),
                ),
              ),
              const SizedBox(width: SnTokens.space2),
              Padding(
                padding: const EdgeInsets.only(top: SnTokens.space2),
                child: OutlinedButton(
                  key: MemberFormScreen.addAllergenKey,
                  onPressed: _busy ? null : _addOther,
                  child: Text(l10n.membersFormAllergenAdd),
                ),
              ),
            ],
          ),
          section(l10n.membersFormConditions),
          for (final k in conditionKeys)
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: Text(conditionLabel(l10n, k)),
              value: _conditions.contains(k),
              onChanged: _busy
                  ? null
                  : (on) => setState(
                      () => on == true
                          ? _conditions.add(k)
                          : _conditions.remove(k),
                    ),
            ),
          section(l10n.membersFormGoal),
          choices(
            goalKeys,
            _goal,
            (k) => goalLabel(l10n, k),
            (v) => _goal = v,
            optional: true,
          ),
          const SizedBox(height: SnTokens.space4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextFormField(
                  key: MemberFormScreen.heightKey,
                  controller: _height,
                  enabled: !_busy,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: InputDecoration(
                    labelText: l10n.membersFormHeightCm,
                    errorMaxLines: 2,
                  ),
                  validator: (v) => _numberError(v ?? '', heightRange),
                ),
              ),
              const SizedBox(width: SnTokens.space3),
              Expanded(
                child: TextFormField(
                  key: MemberFormScreen.weightKey,
                  controller: _weight,
                  enabled: !_busy,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: InputDecoration(
                    labelText: l10n.membersFormWeightKg,
                    errorMaxLines: 2,
                  ),
                  validator: (v) => _numberError(v ?? '', weightRange),
                ),
              ),
            ],
          ),
          section(
            l10n.membersFormCustomAlerts,
            help: l10n.membersFormCustomAlertsHelp,
          ),
          for (final k in customAlertKeys)
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(alertLabel(l10n, k)),
              value: _alerts.contains(k),
              onChanged: _busy
                  ? null
                  : (on) =>
                        setState(() => on ? _alerts.add(k) : _alerts.remove(k)),
            ),
          if (_error case final message?) ...[
            const SizedBox(height: SnTokens.space3),
            InlineErrorBanner(message: message),
          ],
          const SizedBox(height: SnTokens.space5),
          PrimaryButton(
            buttonKey: MemberFormScreen.saveKey,
            label: l10n.membersFormSave,
            icon: Icons.check_rounded,
            busy: _busy,
            onPressed: _save,
          ),
          if (widget.member != null && !_isPrimary) ...[
            const SizedBox(height: SnTokens.space2),
            TextButton.icon(
              key: MemberFormScreen.removeKey,
              style: TextButton.styleFrom(foregroundColor: c.verdictAvoid),
              onPressed: _busy ? null : _remove,
              icon: const Icon(Icons.delete_outline_rounded),
              label: Text(l10n.membersRemove),
            ),
          ],
        ],
      ),
    );
  }
}
