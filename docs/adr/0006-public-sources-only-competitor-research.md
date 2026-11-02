# ADR 0006: Competitor research uses public sources only

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

We want to learn from competitors (Yuka, TruthIn, FactsScan, Xume, HealthifyMe, MyFitnessPal/Cal AI, Fig and others). We evaluated tools from `github.com/topics/reverse-engineer-anything` (REA and its Android forks), which drive JADX, Ghidra and Frida to decompile apps and recover private API schemas.

- MyFitnessPal's terms explicitly forbid reverse engineering, scraping and use for "competitive analysis, or research and development of your own products".
- India's IT Act s.43 covers unauthorised access to or extraction of data.
- Copyright Act s.52 allows decompilation only for interoperability.
- Copying a competitor's code, assets, text or database infringes, and in a trust-sensitive health category the reputational damage would be severe.

## Decision

Competitive research uses **public information only**:
- Store listings, screenshots, release notes and Data Safety forms
- Public reviews
- Official websites, help centres and published scoring methodologies
- Press, blogs and YouTube walkthroughs
- Open data and public API documentation (for example Open Food Facts under ODbL)
- Using the apps as normal consumers under their terms, and recording our own notes on flows

We copy **ideas and patterns, never code, text, images or data**. We will not decompile, intercept or scrape competitor apps or APIs.

REA-style tools may be used only on **our own** builds (for example to check obfuscation or leaked secrets in our APK or web bundle), after approval.

## Consequences

- Findings live in `docs/research/` with source URLs, which keeps a clean-room record.
- Some internals (exact scoring weights, private data sources) stay unknown. We design our own transparent methodology instead, which is itself a differentiator.
- Before shipping any feature closely modelled on a competitor's, do a quick IP check.
