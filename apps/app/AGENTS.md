# apps/app: agent guide

This is the **Android app** for SmartNutri AI, built with Flutter. The web app is a separate Next.js project in `apps/web`, and **both ship every v1 feature** (full parity). Root rules in `../../AGENTS.md` apply first.

> **Current state:** shell built (Plan 2 Task 11): `com.smartnutri.app`, Riverpod 3, `AppConfig` from `--dart-define`, theme from design tokens, generated l10n (en/hi/mr). The old prototype is deleted. New code follows the layout below.

## Stack

- Flutter **3.44.2 stable** (pinned on the dev machine; Dart 3.12.2, so `environment: sdk: ^3.12.0`). Don't upgrade without a deliberate decision.
- `flutter_riverpod` 3 + `riverpod_generator`
- `go_router`, `freezed` + `json_serializable`
- **`smartnutri_api`**: the generated API client in `packages/api-contract/dart` (swagger_parser 1.45). Use it for every API call; never hand-write HTTP calls to the API.
- `drift` (offline log), `flutter_secure_storage`
- `supabase_flutter` 2.18 (Auth: Google OAuth, email OTP or magic link; phone OTP behind a flag)
- `mobile_scanner` (barcode), `image_picker` (camera or gallery), `record` (voice), an audio player for TTS replies
- `flutter_localizations` + ARB files **generated from `packages/i18n`**
- Theme tokens **generated from `packages/design-tokens`**
- `sentry_flutter`, PostHog (no health data in events)
- Lints: `flutter_lints`

## Target `lib/` layout

```
lib/
  main.dart  app.dart  bootstrap.dart
  core/
    config/      # reads --dart-define values (API_BASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, ENVIRONMENT, GOOGLE_WEB_CLIENT_ID, SENTRY_DSN, POSTHOG_KEY, FEATURE_PHONE_OTP)
    network/     # configures the generated smartnutri_api client: base URL, Supabase JWT, retry
    router/      # go_router, auth guard
    theme/       # wraps the GENERATED tokens; no raw colour literals elsewhere
    l10n/        # GENERATED app_{en,hi,mr}.arb (from packages/i18n). Do not edit by hand.
    storage/     # drift database
  features/
    auth/ members/ scan/ product/ analysis/ meals/ history/ voice/ reports/ methodology/ settings/
      └─ each: data/ domain/ presentation/
  shared/widgets/
test/  integration_test/
```

## Generated code: never hand-edit

| Generated | Source of truth | Regenerate |
|---|---|---|
| `packages/api-contract/dart` (`smartnutri_api`) | `packages/api-contract/openapi.json` | `just contract` |
| `lib/core/l10n/app_*.arb` | `packages/i18n/messages/*.json` | `just i18n` |
| Theme tokens (Dart) | `packages/design-tokens/tokens.json` | `just tokens` |

## Configuration

- Config is passed at build time: `--dart-define-from-file=env/<env>.json`. Envs: `dev`, `staging`, `prod`.
- `env/*.json` is **git-ignored**, apart from `env/example.json`, which documents the keys:
  `API_BASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `ENVIRONMENT`, `GOOGLE_WEB_CLIENT_ID`, `SENTRY_DSN`, `POSTHOG_KEY`, `FEATURE_PHONE_OTP`.
  There is no Android client ID key: the Android OAuth client is identified by package name + SHA-1 in Google Cloud and needs no dart-define.
- **No secrets in the app.** The CallMissed key never comes here. All AI and voice calls go through `apps/api`.

## Platform

**Android only for v1** (`android/app/src/main/AndroidManifest.xml`):
- `INTERNET`, `CAMERA`, `RECORD_AUDIO`.
- A Google sign-in redirect intent filter for Supabase OAuth.
- `applicationId` is `com.smartnutri.app`. A final ID will be decided before the Play Store release.

`ios/` is kept so an iPhone build stays possible later, but it is not a v1 target. The `web/`, `linux/`, `macos/` and `windows/` folders are removed: the web app is `apps/web`.

## Rules for this app

- Riverpod only, with feature-first folders. No business logic or HTTP in widgets.
- **Never compute a verdict on the device.** Render exactly what the API returns.
- Every user-facing string goes in `packages/i18n/messages/{en,hi,mr}.json`, then `just i18n`. API reason codes map to `reason_<code>` keys.
- **Verdict UI:**
  - Show the engine status exactly (`ok` / `caution` / `unknown` / `avoid`), using the shared verdict tokens. `unknown` is never green.
  - Show the member's name, the reasons, and "Information, not medical advice".
- Label extraction always goes through an **editable confirm screen** before it is saved.
- Credit Open Food Facts wherever its data is shown.
- **Parity:** each screen has a web counterpart in `apps/web`. Widget tests use the shared cases in `packages/test-fixtures`, so both clients render the same verdicts.

## Commands

From the repo root: `just android`, `just test-app`, `just i18n`, `just tokens`, `just contract`.

From `apps/app`:

| What | Command |
|---|---|
| Dependencies | `flutter pub get` |
| Codegen | `dart run build_runner build --delete-conflicting-outputs` |
| Analyze | `flutter analyze` |
| Tests | `flutter test` |
| Run on Android | `flutter run -d android --dart-define-from-file=env/dev.json` |
| Build Android | `flutter build appbundle --dart-define-from-file=env/prod.json` |

Commit scope: `app`, e.g. `feat(app): scan result screen`.
