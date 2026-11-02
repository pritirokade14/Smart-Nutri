## What & why

<!-- One or two sentences. Link the plan task / milestone (e.g. Plan 2 · Task 4, M1). -->

## Feature parity

- [ ] API change shipped (or not needed)
- [ ] Android (Flutter) shipped (or not needed)
- [ ] Web (Next.js) shipped (or not needed)
- [ ] Shared fixtures in `packages/test-fixtures` pass on all three

## Checklist

- [ ] Tests added/updated and passing (`just test`)
- [ ] Lint clean (`just lint`)
- [ ] Generated code regenerated, not hand-edited (`just contract` / `just i18n` / `just tokens`)
- [ ] New UI strings added to `packages/i18n/messages/{en,hi,mr}.json`
- [ ] No secrets, real user data, or label photos with personal info
- [ ] **Safety:** if scoring, allergen/diet/claim logic, prompts, or verdict/allergy UI changed → `nutrition-safety-reviewer` run and threshold changes explained
- [ ] Migration included if tables or RLS changed (Alembic)
- [ ] ADR added for any significant decision (`docs/adr/`)

## Screenshots (UI changes)

| Android | Web |
|---|---|
|  |  |
