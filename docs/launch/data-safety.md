# Google Play Data safety answers (DRAFT)

> Plan 8 Task 13 Step 2, drafted by Claude. **USER** enters these in Play Console → App content → Data safety (Step 3).
> Check each answer against the shipped build before you submit. If a feature changes, update this file first.

## Overview

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **Yes** |
| Is all of the user data collected by your app encrypted in transit? | **Yes** (HTTPS only) |
| Do you provide a way for users to request that their data be deleted? | **Yes**: in the app (Settings → Delete account) and by web URL `https://app.<domain>/en/privacy#erasure` |
| Is data shared with third parties? | **No**. Service providers acting for us (Supabase, Google Cloud, CallMissed, Sentry, PostHog) are processors, not "sharing" under Play's definition. |
| Ads | **No ads**, no advertising ID |
| Data processed in India | Account and health data: yes (Supabase Mumbai, Cloud Run Mumbai, India-processed AI model for health explanations) |

## Data types

| Play category → type | Collected | Shared | Optional? | Purposes | Notes |
|---|---|---|---|---|---|
| Personal info → **Email address** | Yes | No | Required for email or Google sign-in | Account management | |
| Personal info → **Phone number** | Yes, only when phone OTP is on | No | Optional | Account management | Off at launch (`PHONE_OTP_ENABLED=false`) |
| Personal info → **User IDs** | Yes | No | Required | Account management, analytics | Analytics receive only a one-way hash |
| Personal info → **Name** | Yes | No | Optional | App functionality | Member nicknames for family profiles |
| Health and fitness → **Health info** | Yes | No | Optional (consent `health_data`) | App functionality | Allergies, conditions, diet, goal, height, weight |
| Photos and videos → **Photos** | Yes | No | Optional | App functionality | Label photos, **deleted after 30 days** |
| Audio → **Voice or sound recordings** | Yes | No | Optional | App functionality | The question recording is transcribed and never stored. Spoken answers are deleted after **24 hours**. |
| App activity → **App interactions** | Yes | No | Required | Analytics | Allow-listed events only, with no health data |
| App activity → **Other user-generated content** | Yes | No | Optional | App functionality | Meal logs, products and label values the user confirms, problem reports |
| App info and performance → **Crash logs** | Yes | No | Required | App functionality (stability) | Sentry, with request bodies and personal data scrubbed |
| App info and performance → **Diagnostics** | Yes | No | Required | Analytics | |
| Location, contacts, calendar, SMS, files, web history, financial info | **No** | | | | **Check before you answer "No" for location.** The API strips EXIF (including GPS) before extraction and, since ruling D1/S4, overwrites the stored photo with that EXIF-free re-encode when `POST /v1/scans/label` reads it (rejected uploads are deleted). An upload that is never sent to `/v1/scans/label` still stays in storage for up to 30 days with whatever EXIF the client sent. Both clients must strip EXIF before upload (Android camera and gallery, web file input). Confirm they do. |

"Ephemeral processing" applies to the voice question recording. The label photo is not ephemeral: it is stored for up to 30 days.

## Security practices

- Data is encrypted in transit: **Yes**.
- Users can request deletion: **Yes**.
- Committed to the Play Families Policy: **No**. The app is for adults (target audience **18+**). Adults may add children's profiles.
- Independent security review: **No** (not yet).

## Health apps declaration (Step 3)

- **Type:** a nutrition and wellness **information** app. It is **not a medical device**.
- **Purpose:** it shows whether a packaged food suits each family member, based on rules applied to the product label and on a profile the user enters.
- **Disclaimer:** the app shows "Information, not medical advice" next to every verdict, explanation and voice answer. It does not diagnose, treat, manage or cure any condition.
- **Regulatory status:** not regulated as a medical device. [USER: confirm with the lawyer.]
