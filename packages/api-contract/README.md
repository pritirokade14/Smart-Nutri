# packages/api-contract

The **single source of truth for the API shape** shared by the Android app and the web app. Nothing here is written by hand except this README and the generator configs.

## Contents

| Path | What | Produced by |
|---|---|---|
| `openapi.json` | OpenAPI schema of `apps/api`, **committed** | `apps/api/scripts/export_openapi.py` |
| `dart/` | Dart package **`smartnutri_api`**, used by `apps/app` | [swagger_parser](https://pub.dev/packages/swagger_parser) 1.45 |
| `ts/` | npm package **`@smartnutri/api-client`** (pnpm workspace), used by `apps/web` | [openapi-typescript](https://www.npmjs.com/package/openapi-typescript) 7.13 (types) + [openapi-fetch](https://www.npmjs.com/package/openapi-fetch) 0.17 (runtime) |

## Regenerating

```bash
just contract
```

This exports `openapi.json` from the FastAPI app (no server needed), regenerates `dart/` and `ts/`, and formats them. Commit all three in the **same PR** as the API change.

## Rules

- **Never hand-edit** `openapi.json`, `dart/` or `ts/`. Change the FastAPI schemas or routes, then regenerate.
- **CI fails on drift:** it runs `just contract` and fails if `git diff --exit-code packages/api-contract` is not clean.
- **Stable names:** every route has an explicit `operation_id` (`<feature>_<action>`, e.g. `members_list`). Renaming one is a breaking change for both clients.
- **Breaking changes** (removing or renaming a field or route) need both clients updated in the same PR, or a deprecation period.
- Field names are snake_case on the wire. Don't rename them in the generators.

## Consuming

- **Android:** `apps/app/pubspec.yaml` depends on `smartnutri_api` via `path: ../../packages/api-contract/dart`. `core/network` configures the base URL and the Supabase JWT.
- **Web:** `apps/web/package.json` depends on `"@smartnutri/api-client": "workspace:*"`. `src/lib/api` creates the configured `openapi-fetch` client.
