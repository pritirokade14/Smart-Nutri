# packages/i18n

**Every user-facing string for both clients lives here**, in English, Hindi and Marathi. One source means the Android app and the web app always say the same thing.

## Contents

```
messages/
  en.json   # source language, every key must exist here first
  hi.json   # हिंदी
  mr.json   # मराठी
scripts/    # generator: JSON → Flutter ARB (added with the first slice)
```

Keys are nested by feature, e.g. `scan.confirm.title`, `verdict.status.avoid`, `reason.sugar_high`.

- API **reason codes** map to `reason.<code>`. Every code the rules engine can emit must have a key in all three files.
- Placeholders use ICU syntax (`{name}`, `{count, plural, ...}`), which both next-intl and Flutter ARB understand.

## Consuming

| Client | How |
|---|---|
| Web (`apps/web`) | next-intl imports `messages/<locale>.json` **directly**. No generation step. |
| Android (`apps/app`) | `just i18n` generates `apps/app/lib/core/l10n/app_{en,hi,mr}.arb` (nested keys flattened to camelCase, e.g. `scanConfirmTitle`). Flutter `gen-l10n` then builds the Dart accessors. |

## Rules

- **Add every key to all three files in the same change.** CI checks that the key sets match.
- Never edit the generated ARB files in `apps/app`. Edit here and run `just i18n`.
- Health wording ("Information, not medical advice", verdict labels) must be reviewed by a native speaker before release. Mark unreviewed translations in the PR.
- No HTML in messages. Use rich-text tags supported by both clients only if needed.
