import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_config.dart';
import '../../../core/l10n/app_localizations.dart';
import '../../meals/presentation/meals_providers.dart';
import '../../../core/theme/tokens.g.dart';
import '../../../shared/widgets/buttons.dart';
import '../../../shared/widgets/section_header.dart';
import '../../auth/data/auth_repository.dart';
import '../../consent/presentation/policy_links.dart';
import '../../modes/presentation/mode_switcher.dart';
import '../../modes/presentation/more_menu.dart';
import '../../modes/mode_providers.dart';
import '../../user_types/domain/user_types.dart';
import '../../user_types/presentation/user_type_labels.dart';
import '../../user_types/presentation/user_types_providers.dart';
import 'consents_section.dart';
import 'delete_account_dialog.dart';
import 'settings_providers.dart';

/// Profile tab: language, consents (agree, agree again, withdraw), the
/// privacy policy and terms, signing out and deleting the account (F11).
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  /// [code] null is "device language".
  static Key languageKey(String? code) => Key('language-${code ?? 'system'}');
  static const privacyKey = Key('profile-privacy');
  static const termsKey = Key('profile-terms');
  static const deleteKey = Key('profile-delete-account');
  static const methodologyKey = Key('profile-how-we-score');
  static const userTypesKey = Key('profile-user-types');
  static const guideKey = Key('profile-diary-guide');
  static const myFoodsKey = Key('profile-my-foods');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final hasSite = ref.watch(appConfigProvider).siteUrl.trim().isNotEmpty;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.profileTitle)),
      body: ListView(
        padding: const EdgeInsets.all(SnTokens.space4),
        children: [
          // More first (P9-R6): everything not in the tab bar.
          SectionHeader(title: l10n.modesMoreTitle, icon: Icons.apps_rounded),
          const Card(child: MoreList()),
          const SizedBox(height: SnTokens.space4),
          const _UserTypesSection(),
          const SizedBox(height: SnTokens.space4),
          Card(
            child: Column(
              children: [
                ListTile(
                  key: guideKey,
                  leading: const Icon(Icons.monitor_heart_outlined),
                  title: Text(l10n.settingsDiaryTitle),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => context.push('/profile/guide'),
                ),
                ListTile(
                  key: myFoodsKey,
                  leading: const Icon(Icons.restaurant_menu_rounded),
                  title: Text(l10n.foodsMyFoods),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => context.push('/diary/my-foods'),
                ),
              ],
            ),
          ),
          const SizedBox(height: SnTokens.space4),
          const _LanguageSection(),
          const SizedBox(height: SnTokens.space4),
          const ConsentsSection(),
          const SizedBox(height: SnTokens.space4),
          SectionHeader(
            title: l10n.settingsAboutTitle,
            icon: Icons.info_outline_rounded,
          ),
          Card(
            child: Column(
              children: [
                ListTile(
                  key: methodologyKey,
                  leading: const Icon(Icons.rule_rounded),
                  title: Text(l10n.methodologyTitle),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => context.push('/methodology'),
                ),
                if (hasSite) ...[
                  ListTile(
                    key: privacyKey,
                    leading: const Icon(Icons.privacy_tip_outlined),
                    title: Text(l10n.legalPrivacyTitle),
                    trailing: const Icon(Icons.open_in_new_rounded),
                    onTap: () => openPolicy(context, ref, 'privacy'),
                  ),
                  ListTile(
                    key: termsKey,
                    leading: const Icon(Icons.description_outlined),
                    title: Text(l10n.legalTermsTitle),
                    trailing: const Icon(Icons.open_in_new_rounded),
                    onTap: () => openPolicy(context, ref, 'terms'),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: SnTokens.space4),
          SectionHeader(
            title: l10n.settingsAccountTitle,
            icon: Icons.manage_accounts_rounded,
          ),
          SecondaryButton(
            label: l10n.authSignOut,
            icon: Icons.logout_rounded,
            onPressed: () => signOutClearingQueue(
              ref.read(authRepositoryProvider),
              ref.read(mealQueueProvider),
            ),
          ),
          const SizedBox(height: SnTokens.space2),
          TextButton.icon(
            key: deleteKey,
            style: TextButton.styleFrom(
              foregroundColor: theme.colorScheme.error,
            ),
            icon: const Icon(Icons.delete_forever_outlined),
            label: Text(l10n.settingsDeleteButton),
            onPressed: () => showDeleteAccountDialog(context),
          ),
        ],
      ),
    );
  }
}

/// "Change your focus": the user types (the same screens as onboarding,
/// prefilled). Editing them never changes a member by itself.
class _UserTypesSection extends ConsumerWidget {
  const _UserTypesSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final out = ref.watch(userTypesProvider).value;
    final names = out == null
        ? ''
        : [for (final t in chosenTypes(out)) modeName(l10n, t)].join(', ');
    final switcher = ref.watch(chosenTypesProvider).length >= 2;
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ListTile(
            key: ProfileScreen.userTypesKey,
            leading: const Icon(Icons.tune_rounded),
            title: Text(l10n.userTypesEdit),
            subtitle: names.isEmpty ? null : Text(names),
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => context.push('/welcome?edit=1'),
          ),
          if (switcher)
            const Padding(
              padding: EdgeInsets.fromLTRB(
                SnTokens.space4,
                0,
                SnTokens.space4,
                SnTokens.space4,
              ),
              child: ModeSwitcher(showNote: true),
            ),
        ],
      ),
    );
  }
}

/// The app language: the device's, or one of en, hi, mr.
class _LanguageSection extends ConsumerWidget {
  const _LanguageSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final selected = ref.watch(appLocaleProvider)?.languageCode;
    final options = <(String?, String)>[
      (null, l10n.settingsLanguageSystem),
      ('en', l10n.languageEn),
      ('hi', l10n.languageHi),
      ('mr', l10n.languageMr),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(title: l10n.languageLabel, icon: Icons.translate_rounded),
        Card(
          child: RadioGroup<String>(
            groupValue: selected ?? '',
            onChanged: (code) => ref
                .read(appLocaleProvider.notifier)
                .select(code == null || code.isEmpty ? null : code),
            child: Column(
              children: [
                for (final (code, label) in options)
                  RadioListTile<String>(
                    key: ProfileScreen.languageKey(code),
                    value: code ?? '',
                    title: Text(label),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
