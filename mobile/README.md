# Ardhang Matrimony — Mobile App (Expo SDK 57)

Production-ready React Native (Expo) client for the **Matchmaking API**. The
backend (FastAPI) is the source of truth for all data, authorization,
subscription/verification state, pricing and privacy. This app only renders
that state.

## Stack

- Expo SDK 57 (React Native 0.86, React 19, TypeScript)
- React Navigation 7 (native stack + bottom tabs, custom branded drawer)
- TanStack Query 5 for server state
- expo-secure-store (tokens), expo-image-picker + signed-upload flow
- expo-image / FlashList for lists and images

## Setup

```bash
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_BASE_URL for your environment
npm run start          # Expo dev server
npm run android        # Android emulator (uses http://10.0.2.2:8000 default)
npm run ios            # iOS simulator
npm run typecheck      # tsc --noEmit
```

## Environment / config

`src/config/env.ts` centralizes the API base URL and environment
(`development` | `staging` | `production`). Values come from `EXPO_PUBLIC_*`
env vars, falling back to `app.json` `extra` and per-env defaults. No secrets
live here.

## Remote configuration

On startup the app loads local defaults → cached config → `GET /api/v1/app/config`
and applies branding/theme/features. Remote config never blocks launch and
never carries secrets. Components read theme/branding through `useTheme()` /
`useRemoteConfig()` — no hard-coded hex values in components.

## Architecture

```
src/
  api/          typed API modules over a single client (refresh/401/errors)
  auth/         session context (secure token storage, restore, sign-out)
  components/   design-system primitives (button, card, states, sheets, …)
  config/       env + RemoteConfigProvider
  features/     screens grouped by feature (auth, profile, matches, chat, …)
  hooks/        shared hooks
  navigation/   RootNavigator (protected) → Auth / App navigators
  query/        TanStack Query client + query keys
  storage/      secure token storage + remote-config cache
  theme/        colors/typography/spacing/radius/shadows + ThemeProvider
  types/        API + domain models (mirrors backend schemas)
  utils/        formatting, validation, image-url normalization, upload
```

## Backend contract notes

- Response envelope: `{ data, meta }`; errors: `{ error: { code, message } }`.
- Auth: `POST /auth/register` accepts `email` (+ optional `phone_number`) and
  `password` only — first/last name are stored via the profile on onboarding.
- Recommendations return candidate IDs + scores; this app resolves each into a
  public profile via `GET /profiles/{user_id}`.
- Photo upload uses the backend signed-upload flow
  (`POST /profile/photos/upload-url` → PUT → `POST /profile/photos/confirm`).
- Premium/filter/messaging entitlement is always read from backend endpoints
  (`GET /subscription`, error codes like `PREMIUM_REQUIRED`). See
  `README` limitations in the final report for known backend gaps.
