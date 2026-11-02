# SmartNutri Android App (Flutter)

The SmartNutri AI Android app: scan packaged food, get a verdict for each family member, and log what you eat. The web app with the same features is in [`apps/web`](../web/README.md).

> The v1 rebuild is in progress. `lib/` is still the prototype until Plan 3 rebuilds it.

## Setup

Requirements: Flutter latest stable (`flutter upgrade`), and Android Studio or an Android device.

```bash
cd apps/app
flutter pub get
```

From the repo root, `just setup` also runs `just contract`, `just i18n` and `just tokens`, which generate the API client, the ARB string files and the theme tokens this app imports.

Create `env/dev.json` from `env/example.json` (added in Plan 3):

```json
{
  "ENV": "dev",
  "API_BASE_URL": "http://10.0.2.2:8000",
  "SUPABASE_URL": "https://<project>.supabase.co",
  "SUPABASE_PUBLISHABLE_KEY": "<sb_publishable_... key>",
  "SENTRY_DSN": "",
  "POSTHOG_KEY": ""
}
```

On the Android emulator, `10.0.2.2` points at your computer's `localhost`.

## Run

```bash
just android
# or, from apps/app:
flutter run -d android --dart-define-from-file=env/dev.json
```

## Test

```bash
just test-app
# or, from apps/app:
flutter analyze && flutter test
```

See [AGENTS.md](AGENTS.md) for the folder layout, generated-code rules and coding rules.
