---
name: flutter-feature
description: Use when adding or changing a feature, screen, provider, repository or route in apps/app (the Flutter Android app), including localisation strings, theme tokens and widget tests.
---

# Adding a Flutter (Android) feature

The stack is Flutter stable, Riverpod 3 (with `riverpod_generator`), go_router, freezed, drift, supabase_flutter, and the **generated API client `smartnutri_api`** (`packages/api-contract/dart`). See `apps/app/AGENTS.md`. The same feature is built for the web in `apps/web` (full parity), usually in parallel.

## Folder shape (feature-first)

```
lib/features/<feature>/
  data/          <feature>_repository.dart  (wraps smartnutri_api calls, maps to domain)
  domain/        <thing>.dart (freezed models, no Flutter imports)
  presentation/  <feature>_screen.dart, widgets/, <feature>_providers.dart
test/features/<feature>/   repository_test.dart, providers_test.dart, <feature>_screen_test.dart
```

## Steps

1. **Check that the contract is current.** The API endpoint must exist, and `just contract` must have been run. Never hand-write HTTP calls or DTOs for our API; use `smartnutri_api`.
2. **Domain model** in `domain/`, using `@freezed`. Map from the generated client types in the repository. Run:
   `dart run build_runner build --delete-conflicting-outputs`
3. **Repository** in `data/`.
   - Takes the configured `smartnutri_api` client from `core/network`, which already handles the base URL, the Supabase JWT and retry.
   - Returns domain models, and maps API errors (`error.code`) to typed failures. No `print`.
4. **Providers** in `presentation/<feature>_providers.dart`. Use `@riverpod`, and expose async state as `AsyncValue`. Tests override the repository.
5. **Screen.** It reads providers and renders the loading, error (with retry) and data states. **No business logic, HTTP or verdict computation in widgets.**
6. **Route** in `core/router/` with go_router. Auth-guarded routes go under the signed-in shell.
7. **Strings:**
   - Add keys to `packages/i18n/messages/{en,hi,mr}.json` (all three) and run `just i18n`. That regenerates the ARB files; never edit them by hand.
   - Use `context.l10n.<key>`. API reason codes map to `reason.<code>`.
8. **Styling:** use the generated tokens via `core/theme` only (`just tokens` after token changes). No raw colours.
9. **Tests:**
   - Widget tests for all three `AsyncValue` states with a fake repository.
   - For verdict screens, use the shared cases in `packages/test-fixtures`.
   - A repository unit test with a mocked client.
10. **Check:** `flutter analyze && flutter test`, then run on an Android emulator or device (`just android`).

## Android rules

- Permissions are declared in the manifest: `CAMERA` (barcode and label), `RECORD_AUDIO` (voice), `INTERNET`. Ask at the moment of use, with a rationale string from `packages/i18n`.
- Images: `image_picker`, compressed before upload (max 8 MB). Voice: `record`, max 30 s.
- Config comes from `--dart-define-from-file=env/<env>.json` via `core/config`. **Never put secrets in the app.**

## Verdict UI rules (health app)

- Show the engine status exactly (`ok` / `caution` / `unknown` / `avoid`) using the verdict tokens. `unknown` is never green.
- An allergy `unknown` says "We couldn't read the ingredients. Check the pack."
- Each verdict shows its reasons, the member's name, and "Information, not medical advice".
- Label extraction results open in an **editable confirm screen** before they are saved.
- Credit Open Food Facts on any screen that shows its data.

## Pitfalls

- Mixing `Provider` (the prototype) and Riverpod. Use Riverpod only.
- Editing generated code (`smartnutri_api`, ARB files, tokens). Your change will be overwritten.
- Building a screen the web doesn't have. Coordinate parity with the `web-feature` work for the same slice.
