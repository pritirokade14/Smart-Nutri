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

## Token groups

| Group | Tokens | Use |
|---|---|---|
| `color.verdict.*` | `ok`, `caution`, `avoid`, `unknown` | Solid verdict colour (badges, borders). Pinned. |
| `color.surface.verdict.*` | same four | Light tint behind a verdict card header. |
| `color.brand.*` | `primary`, `soft`, `strong` | The one brand accent (jamun purple): primary actions, selection, links. Never green, never a verdict colour. |
| `color.accent.*` | `warm`, `peach` | Decorative only (illustrations, icon tiles). Never carries meaning. |
| `color.text.*` | `primary`, `secondary`, `inverse` | Body text, muted text, text on brand/verdict fills. |
| `color.surface.*` | `default`, `canvas`, `muted` | Cards, the warm page background, chips and skeletons. |
| `color.border.*` | `default`, `strong` | Hairlines, input outlines. |
| `color.grade.*` | `a`–`e` | Nutri-Score letters (calculated by SmartNutri). |
| `color.google.*` | logo colours, `surface`, `border`, `text` | The "Continue with Google" button, per Google's branding guidelines. |
| `color.dark.*` | mirrors the groups above | The dark theme. Dark verdict colours are lighter so they stay AA on dark surfaces; `dark.verdict.unknown` is grey. |
| `space.1`–`space.8` | 4, 8, 12, 16, 24, 32, 48, 64 px | Spacing scale. |
| `radius.*` | `sm` 4, `md` 8, `lg` 16, `xl` 24, `full` 999 px | Corner radii. |
| `elevation.*` | `none` 0, `low` 1, `medium` 3, `high` 6 px | Shadow depth (Material elevation on Android). |
| `font.size.*` | `xs` 12 … `3xl` 34 px | Type scale. Android bundles Mukta (Latin + Devanagari). |

`scripts/tokens.test.mjs` checks WCAG AA for every text, brand and verdict colour on its backgrounds (light and dark) and that no `unknown` colour or brand colour is green.

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
