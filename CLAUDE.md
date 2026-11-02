@AGENTS.md

# Claude Code specifics

## Skills in this repo (`.claude/skills/`)

| Skill | Use when |
|---|---|
| `scoring-rule` | Adding or changing anything in `apps/api/app/scoring` (rules, thresholds, allergen and diet terms), including the expected verdicts in `packages/test-fixtures` |
| `callmissed` | Calling the CallMissed API: LLM, vision extraction, STT, TTS, WhatsApp, email |
| `api-endpoint` | Adding or changing a FastAPI endpoint in `apps/api/app/features/<f>/` |
| `api-contract` | Exporting `openapi.json`, regenerating the Dart and TypeScript clients, fixing contract drift |
| `flutter-feature` | Adding a feature or screen in the Android app (`apps/app`) |
| `web-feature` | Adding a feature, page or component in the web app (`apps/web`) |
| `label-eval` | Measuring label-extraction accuracy on the evaluation photo set |

## Subagents in this repo (`.claude/agents/`)

| Agent | Model | Use for |
|---|---|---|
| `nutrition-safety-reviewer` | opus | Review **every** change touching scoring, allergens, diet, claims, prompts, test fixtures, or verdict and allergy UI on Android or web, before merge |
| `api-builder` | sonnet | Implementing plan tasks in `apps/api` (and running `just contract`) |
| `flutter-builder` | sonnet | Implementing plan tasks in `apps/app` (Android) |
| `web-builder` | sonnet | Implementing plan tasks in `apps/web` (Next.js) |

**Model choice:** use Sonnet for small, routine tasks. Use Opus for architecture, tricky debugging and code review. Set `model:` explicitly when spawning subagents.

## Executing plans (vertical slices)

- Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` with the plans in `docs/superpowers/plans/`. Tick checkboxes as tasks complete.
- For each feature slice:
  1. `api-builder` implements the endpoint and runs `just contract`.
  2. Then run **`flutter-builder` and `web-builder` in parallel** against the regenerated clients. Their files are disjoint (`apps/app` vs `apps/web`).
  3. Then `nutrition-safety-reviewer` reviews the whole slice if it touches verdicts, allergies, prompts or fixtures.
- A slice is done only when `just test` passes and the shared fixtures pass on API, Android and web.
