# ADR 0005: The rules engine decides; the LLM only explains

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

Users with diabetes, hypertension, allergies or young children act on our verdicts. LLMs can hallucinate numbers and verdicts, give different answers to the same input, and be talked out of a verdict by prompt injection (for example through a voice question). The prototype had fake fallback data shown as real, a home-made "Nutri-Score", and allergen matching on substrings only.

## Decision

All verdicts, scores, allergen states, diet violations and claim checks come from a **deterministic, unit-tested rules engine** (`apps/api/app/scoring`). The LLM receives the engine's output and may only explain it, suggest how to eat the food, and translate.

- Thresholds live in versioned YAML files, marked `PENDING CLINICIAN REVIEW` until a clinician signs off.
- Reasons are codes with params, never prose, so they can be localised and tested.
- Unknown or missing data produces `unknown`, never `ok`. An allergic member is never `ok` when ingredients are unknown.
- Label extraction by the LLM is **input data**, not a verdict. The user confirms it, and implausible values are dropped.

## Consequences

- Verdicts are testable, reproducible and explainable on the public "How we score" page.
- Prompt injection cannot change a verdict.
- Rules must be written and maintained by hand, so nuance arrives more slowly than with a "just ask the model" approach. Every new condition needs data, tests and a review.
- Copy and UI must show the engine's verdict, with the LLM text visually secondary.
- Any PR touching `scoring/`, prompts or the verdict UI must be reviewed by the `nutrition-safety-reviewer` agent.
