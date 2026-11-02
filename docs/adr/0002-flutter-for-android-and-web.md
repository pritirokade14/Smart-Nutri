# ADR 0002: Flutter for the Android app and the web app

- **Status:** Superseded by ADR 0008 (2026-11-02): the web app is now Next.js, and Flutter targets Android only.
- **Date:** 2026-11-02

## Context

v1 must ship an Android app (most Indian users) and a web app within about 15 days. The prototype is already in Flutter. The alternatives were React Native plus Next.js (two codebases), Kotlin Multiplatform (no mature web target), or a native Android app plus a separate web app.

## Decision

Keep **Flutter** and build Android and web from one codebase.
- Use a feature-first structure with Riverpod, go_router, dio, drift and ARB localisation.
- iOS comes later from the same code.
- For the web, use only plugins that support it (`mobile_scanner` works on web; avoid `dart:io` `File` in shared code).

## Consequences

- One team, one codebase and one set of widgets. The web app comes almost for free.
- The web build is static files, hosted on Firebase Hosting (free tier, CDN, in the same Google Cloud project as the API).
- Flutter web is weaker for SEO and its first load is heavy. That is acceptable for a logged-in app. The public "How we score" page can also be served as static HTML from the API.
- A richer B2B dietitian dashboard in v2 may justify a separate web stack (for example Next.js). That will need its own ADR.
- The prototype's Provider and `setState` code is replaced. Riverpod providers must stay free of UI code so they can be tested.
