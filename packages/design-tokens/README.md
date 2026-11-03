# packages/design-tokens

Colours, typography, spacing and radii shared by the Android app and the web app, so both look like one product. **Verdict colours live here**, so `ok` / `caution` / `unknown` / `avoid` look the same everywhere.

## Contents

```
tokens.json             # source of truth (W3C design-token format)
style-dictionary.config.mjs
build/                  # GENERATED, don't edit
  dart/tokens.dart      # copied into apps/app/lib/core/theme/
  css/tokens.css        # CSS variables, imported by apps/web (Tailwind 4 @theme)
```

## Generating

```bash
just tokens
```

This runs [Style Dictionary](https://www.npmjs.com/package/style-dictionary) 5 and writes the Dart and CSS outputs.

## Rules

- **Verdict tokens are safety-relevant:**
  - `color.verdict.ok` is green.
  - `color.verdict.caution` is amber.
  - `color.verdict.avoid` is red.
  - `color.verdict.unknown` is **grey and must never be green**.
  - Changing them needs a `nutrition-safety-reviewer` pass.
- Meet WCAG AA contrast for text on every background token. Many users are older and read on low-end screens.
- No raw colour or spacing literals in either client. Add a token here instead.
- **Semantic palette:** `color.brand.{primary,strong,on,soft}`, `color.surface.{canvas,default,muted}`, `color.border.default`, `color.text.{primary,secondary,inverse}`, `color.verdict.soft.*` (tint behind a verdict) and `color.grade.on.*` (text on a Nutri-Score tile). The brand accent is a teal-blue that must never read as a verdict colour (tested: not green, far from every verdict colour).
- **Dark mode:** `color.dark.*` mirrors the semantic names (brand, surface, border, text, verdict, verdict.soft). The web swaps them in under `prefers-color-scheme: dark` (`apps/web/src/app/globals.css`); Android reads them as `SnTokens.dark*`. Grade colours and `grade.on.*` are not swapped. `color.dark.verdict.unknown` is grey and never green.
- Never edit the generated `build/` files or their copies in the apps.
- CSS uses Tailwind 4 theme namespaces: `font.size.*` becomes `--text-*`, `space.*` becomes `--spacing-*`, `radius.*` stays `--radius-*`. Our spacing and radius scales **intentionally override the Tailwind defaults** (for example `p-5` is 24px and `rounded-lg` is 16px).
