@AGENTS.md

# Claude Code in apps/api

- Skills:
  - `scoring-rule` for anything in `app/scoring` (including `packages/test-fixtures` expectations).
  - `api-endpoint` for routes, schemas, models, services and migrations in `app/features/<f>/`.
  - `api-contract` after any route or schema change (export `openapi.json`, regenerate both clients).
  - `callmissed` for LLM, vision, STT, TTS, WhatsApp and email.
  - `label-eval` for extraction model or prompt changes.
- Subagents:
  - `api-builder` (sonnet) implements plan tasks here and runs `just contract`.
  - `nutrition-safety-reviewer` (opus) must review any change to scoring, prompts, fixtures or calls that include health data.
- After an API slice lands, `flutter-builder` and `web-builder` build the client side in parallel against the regenerated clients.
- Active plan: `docs/superpowers/plans/2026-11-02-plan-1-rules-engine.md`. Work task by task and tick the checkboxes.
