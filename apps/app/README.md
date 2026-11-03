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
  "ENVIRONMENT": "dev",
  "API_BASE_URL": "http://10.0.2.2:8000",
  "SUPABASE_URL": "https://<project>.supabase.co",
  "SUPABASE_PUBLISHABLE_KEY": "<sb_publishable_... key>",
  "GOOGLE_WEB_CLIENT_ID": "",
  "SENTRY_DSN": "",
  "POSTHOG_KEY": "",
  "FEATURE_PHONE_OTP": "false",
  "FEATURE_EMAIL_OTP": "false",
  "SITE_URL": "<web app origin, e.g. the dev web URL>",
  "FEATURE_VOICE": "false"
}
```

`SITE_URL` is the public web app origin. The privacy and terms links and the share link use it, and they are hidden when it is empty. `FEATURE_VOICE` shows push-to-talk; keep it `false` until the API runs with `VOICE_ENABLED=true`.

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
