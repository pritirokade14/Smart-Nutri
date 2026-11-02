@AGENTS.md

# Claude Code in apps/app (Android)

- Skill: `flutter-feature`, for every new feature, screen, provider or route.
- Related skill: `api-contract` if the generated `smartnutri_api` client looks out of date. Don't hand-edit it; regenerate with `just contract`.
- Subagents:
  - `flutter-builder` (sonnet) implements plan tasks here. It usually runs **in parallel with `web-builder`** on the same feature slice.
  - `nutrition-safety-reviewer` (opus) must review any change to verdict, allergy or analysis UI.
- Verify on an Android emulator or device before claiming done. The web counterpart lives in `apps/web`, not here.
