@AGENTS.md

# Claude Code in apps/web

- Skill: `web-feature`, for every new page, feature, component or route.
- Related skill: `api-contract` if `@smartnutri/api-client` looks out of date. Don't hand-edit it; regenerate with `just contract`.
- Subagents:
  - `web-builder` (sonnet) implements plan tasks here. It usually runs **in parallel with `flutter-builder`** on the same feature slice.
  - `nutrition-safety-reviewer` (opus) must review any change to verdict, allergy or analysis UI, and any public page that shows product data.
- Verify before claiming done: `pnpm test`, `pnpm tsc --noEmit`, `pnpm biome check .`, and the relevant Playwright spec (`just e2e`).
