# Competitor Research Method and Policy

**Date:** 2026-11-02

**Key takeaways**
- The GitHub topic `reverse-engineer-anything` is built around **REA**, an MCP/CLI that lets AI agents drive Ghidra, IDA, Hopper and JADX. **None of its 13 repos is a feature-teardown tool.** The two relevant ones decompile apps or recover private API schemas.
- Using them on competitors carries real legal risk.
  - MyFitnessPal's terms explicitly ban reverse engineering, scraping and "competitive analysis".
  - India's IT Act s.43 covers unauthorised access or extraction.
  - Copyright Act s.52 only permits decompiling for interoperability.
- **Our policy:** a clean-room teardown from **public sources only**. We copy ideas, never code, data, text or assets.
- Everything we need (journeys, features, pricing, complaints) is available from store listings, help centres, reviews, videos, and using each app as a normal user.

## The `reverse-engineer-anything` topic (13 repos, fetched 2026-11-02)

| Repo | What it is | Useful to us? |
|---|---|---|
| AIshihzong/awesome-reverse-engineer-anything (391★) | Curated list of AI-driven reverse-engineering and rebuild case studies. Its README says "public information only" and "governed by local law, licences and ToS" | No |
| smartworldarafath/REA_Skill | 243 agent skills for decompiling APK/IPA/Electron/web bundles, PCAP, and protobuf/gRPC schema recovery | **No.** This is the prohibited activity |
| Hubupup/REA-ReverseEngineerAndroid | Android REA fork with 117 MCP tools wrapping JADX, Apktool, Frida, ADB and Ghidra. "Only for software you own or are authorised to analyse" | Only on **our own** APK, for security and obfuscation checks, and only with approval |
| aslamambiloly/stealth_enum_workspace | Strips enum metadata from Flutter AOT builds | Possibly to harden our own build |
| Other 9 (game clones, curated lists, a screensaver, a mouse configurator, Homebrew tap) | Unrelated | No |

Repo details beyond 4 READMEs come from the topic page only [unverified].

## Legal and ethical risk (summary, not legal advice)

- **App terms of service:**
  - MyFitnessPal bans reverse engineering, derivative works, scraping, bots, bypassing access controls, and use for "competitive analysis or R&D of your own products".
  - HealthifyMe's terms page returned 403 [unverified]. Yuka has no confirmed clause [unverified].
  - Installing an app means accepting its terms, so breaching them risks takedowns, account bans or a lawsuit.
- **IT Act 2000 s.43 and s.66:** unauthorised access, extraction or copying of data carries damages and offences. Calling private APIs or bypassing protections could fall under them.
- **Copyright Act 1957 s.52(1)(aa)/(ab):** decompiling is allowed only to achieve interoperability. Copying code, assets, UI or database content infringes.
- **Databases:** India has no special database right, but a compilation can be protected as a literary work, and terms of service still apply. Bulk-scraping a food database is the highest-risk activity.
- **Google Play DDA:** apps must not infringe others' IP, and Google can suspend developers.
- **Reputation:** in a trust-based health category, being caught using a rival's private API or data would be very damaging.

## Our policy

**Allowed (public, clean-room):**
- Play Store and App Store listings: screenshots, "what's new", pricing, permissions, Data Safety forms.
- Mining public reviews for pain points.
- Public help centres, FAQs, methodology pages and blogs (for example Yuka's scoring and independence pages).
- YouTube walkthroughs, influencer reviews and marketing sites.
- **Using each app ourselves as a normal user**, under its terms. We record our own screen and write up the flows.
- Public API docs and open data: Open Food Facts (ODbL), FSSAI and ICMR-NIN.
- Job posts, tech blogs and Wayback Machine snapshots of public pages.

**Forbidden:**
- Decompiling or disassembling competitor apps (APK/IPA), or running JADX, Frida or REA tools against them.
- Intercepting their network traffic, or calling their private APIs.
- Scraping or bulk-downloading their product databases or content.
- Copying their text, scoring tables, images, icons, UI assets or code.

**Guardrails:**
- Keep a short clean-room log in `docs/research/`: who observed what, from which public source, and on what date.
- Write features from our own requirements. Note "inspired by X" in the doc, not in the code.
- Get a legal review before anything closely resembles a competitor's distinctive feature or design.
- REA-style tools are used only on SmartNutri's own builds (for example obfuscation and secret-leak checks), and only after the founder approves.

## Sources

- **Topic page:** https://github.com/topics/reverse-engineer-anything
- **Curated list:** https://github.com/AIshihzong/awesome-reverse-engineer-anything
- **Android REA fork:** https://github.com/Hubupup/REA-ReverseEngineerAndroid
- **REA_Skill:** https://github.com/smartworldarafath/REA_Skill
- **MyFitnessPal terms:** https://www.myfitnesspal.com/terms-of-service
- **Yuka terms:** https://help.yuka.io/l/en/article/c1zr4m81g1
- **India Code (IT Act, Copyright Act):** https://www.indiacode.nic.in/
- **Google Play DDA:** https://play.google.com/about/developer-distribution-agreement.html
