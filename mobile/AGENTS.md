# AGENTS.md — Ardhang Matrimony Mobile (Expo SDK 57)

Guidance for AI agents and developers working on the **mobile** Expo application in this repository. It is a client for the FastAPI backend at the repo root — **the backend and its `AGENTS.md` are the source of truth for all API contracts, authorization, subscription/verification/payment state, pricing and privacy.**

Read this file before modifying anything in `mobile/`.

---

## 1. What this project is

- Expo SDK 57 (React Native 0.86, React 19, TypeScript strict) — run via `npm start` / Expo Go or a dev build.
- React Navigation 7 (native-stack + bottom tabs; the hamburger menu is a custom `MenuDrawer`, not the drawer navigator).
- TanStack Query v5 for all server state; React context for session/auth, theme and remote config.
- expo-secure-store for auth tokens (never plain AsyncStorage for secrets); AsyncStorage only for the remote-config cache.
- expo-image-picker + the backend signed-upload flow for photos.

**Golden rule:** the backend is authoritative. The mobile app never re-implements business rules, never trusts client-supplied premium/verification/payment state, and never fabricates API responses. Feature gating in the UI is convenience only.

---

## 2. Repo layout

```text
mobile/
├── app.json                 # Expo config, plugins, extra (env defaults)
├── package.json             # deps + scripts (typecheck = tsc --noEmit)
├── tsconfig.json            # extends expo/tsconfig.base, strict
├── index.ts                 # registerRootComponent(App)
├── App.tsx                  # providers: Query → SafeArea → RemoteConfig → Theme → Auth → RootNavigator
├── .env.example             # EXPO_PUBLIC_APP_ENV / EXPO_PUBLIC_API_BASE_URL
└── src/
    ├── api/                 # typed API modules over client.ts + lookups.ts (UI option sets)
    ├── auth/                # AuthContext (restore/signIn/signOut) + useAuth
    ├── components/          # design-system primitives (see §6)
    ├── config/              # env.ts + RemoteConfigProvider
    ├── features/            # screens per feature (auth, profile, matches, chat, alerts, premium, horoscope, services, settings, dashboard)
    ├── hooks/               # shared hooks (useDebounce)
    ├── navigation/          # RootNavigator, AuthNavigator, AppNavigator, MainTabs, types.ts
    ├── query/               # queryClient + queryKeys
    ├── storage/             # tokenStorage.ts (SecureStore), configCache.ts (AsyncStorage)
    ├── theme/               # colors/typography/spacing/radius/shadows + theme.ts + ThemeProvider
    ├── types/               # api.ts (ApiError), models.ts (domain), enums.ts, remoteConfig.ts
    └── utils/               # format.ts, validators.ts, imageUrl.ts, upload.ts
```

---

## 3. Commands (run from `mobile/`)

```bash
npm install                 # install deps
npm run start               # Expo dev server
npm run android             # Android (default dev API http://10.0.2.2:8000)
npm run ios                 # iOS simulator (macOS only)
npm run typecheck           # tsc --noEmit  (this is the lint gate)
npx expo-doctor             # dependency/version health checks
npx expo export --platform android   # verifies the app bundles (Metro)
```

There is deliberately **no `babel.config.js`** — adding one breaks `babel-preset-expo` resolution (it is nested under `expo`). Rely on Expo's defaults. If you must add a babel config, reference the preset via `require.resolve('expo/../babel-preset-expo')` or move it to root `devDependencies`.

**CI definition of done:** `npm run typecheck` clean, `npx expo-doctor` clean, `npx expo export --platform android` bundles.

---

## 4. Backend integration rules

- The API base URL is `API_URL = <base>/api/v1` from `src/config/env.ts` (env var → app.json `extra` → per-env default). Never hard-code `http://localhost:8000` in screens.
- The backend responds with `{"data": ..., "meta": {...}}`; errors are `{"error": {"code", "message", "details?"}}`. Everything goes through `src/api/client.ts` (`apiRequest`) which attaches the access token, refreshes once on 401, and normalizes failures into `ApiError` (code + status). **Never call `fetch()` in components.**
- Auth tokens are saved/loaded via `src/storage/tokenStorage.ts` (expo-secure-store). Refresh rotation and `TOKEN_REVOKED` are handled server-side; the client clears the session via the `onAuthExpired` listener when refresh fails.
- When the backend returns premium-gated codes (`PREMIUM_REQUIRED`, `MESSAGE_LIMIT_REACHED`, `UPGRADE_REQUIRED`), the app shows the upgrade flow (see `ApiError.isPremiumGated`). Do not pre-empt the backend with local entitlement logic.
- If an endpoint does not exist, check `src/api/` and the backend routers first. If genuinely missing, surface an honest "not available yet" UI and document it — never fake a backend response.

---

## 5. Remote configuration & theming

- `RemoteConfigProvider` (`src/config/RemoteConfigProvider.tsx`) implements: load local defaults → load cached config → `GET /api/v1/app/config` → validate/normalize → apply. **Fail-open**: a failure must never block launch.
- `ThemeProvider` (`src/theme/ThemeProvider.tsx`) builds the theme from `branding.*` overrides. Components must read colors via `useTheme()` — **never hard-code hex values** (e.g. `color="#7A1730"`) in components.
- Brand/app copy (name, tagline, feature flags, limits, display pricing, maintenance, versions, legal/support) must come from `useRemoteConfig()`, with `DEFAULT_REMOTE_CONFIG` fallbacks — never hard-coded per-screen.
- Maintenance mode (`config.app.maintenance_mode`) is rendered by `MaintenanceScreen` in `RootNavigator`.
- The backend's `app/services/app_config_keys.py` is the source of truth for known config keys; the public response groups by category (`branding`, `app`, `features`, `limits`, `pricing`, `versions`, `legal`, `support`).

---

## 6. Component & UI conventions

Reusable primitives live in `src/components/`:

`AppText` (all typography via variants), `AppButton` (variants + loading), `AppInput` (label/error/secure toggle/left icon), `AppCard`, `ProfileAvatar` (initials fallback + online dot), `VerifiedBadge`, `FilterChip`, `ProfileCard` (discovery grid), `SectionHeader`, `LoadingState`, `EmptyState`, `ErrorState` (branded — never raw errors/stack traces/SQL), `NotificationBadge`, `PremiumBadge`, `SubscriptionCard`, `BottomSheet`, `Modal`, `MenuDrawer`, `CollapsibleSection`, `PasswordStrengthIndicator`, `ScreenContainer` (safe areas + keyboard avoidance), `AppHeader`, `AppIcon` (Ionicons wrapper).

Rules:
- Build on these components; do not sprinkle ad-hoc `Text`/`Button` styles across features.
- `ErrorState` must never display raw API messages/stack traces/internal details.
- Loading/empty/error states are required on every API-driven screen.
- Use FlatList/FlashList for any list that can grow; paginate (matches, messages, notifications). Do not render thousands of items at once.
- Communicate with color **and** text (accessibility): e.g. password strength, verified badges, unread indicators.

---

## 7. State management

- **Server state → TanStack Query.** Query keys are centralized in `src/query/keys.ts`. Hooks live next to their feature in `src/features/<feature>/hooks.ts` (e.g. `useOwnProfile`, `useFeed`, `useMessages`, `useSubscription`). Prefer `queryClient.setQueryData`/`invalidateQueries` over manual refetch.
- **Local/UI state → React context or component state.** The only contexts are: `AuthProvider`, `RemoteConfigProvider`, `ThemeProvider`, TanStack `QueryClientProvider`. Do not create a giant global store.
- Optimistic updates are acceptable for chat sends (roll back on error) — see `useSendMessage`.

---

## 8. Navigation structure

```text
RootNavigator (protected)
├── Loading / Maintenance  (session restore / backend maintenance flag)
├── AuthNavigator          (Welcome, Login, Register, ForgotPassword)
└── AppNavigator
    ├── MainTabs           (Profile, Matches, Chat, Alerts, Premium)
    ├── Dashboard, ProfileDetails, EditProfile, Photos, MatchFilters,
    │   ChatConversation, HoroscopeMatch, Services, Settings,
    │   HelpSupport, Referral, More, JobVerification
```

- Route params are typed in `src/navigation/types.ts`. **Never trust a `userId` from navigation params for authorization** — the backend enforces ownership; the screen is only allowed to request data for that id.
- Users who are not authenticated must never reach `AppNavigator`.

---

## 9. Security invariants (do not break)

- Never store passwords. Store tokens only via `expo-secure-store`.
- No API secrets / payment credentials / `JWT_SECRET_KEY` in the app or in `EXPO_PUBLIC_*` vars.
- Never trust the client for premium/subscription/payment/verification status or admin role — always from the backend (`GET /subscription`, etc.).
- Never expose private fields in UI beyond what the backend response shape provides (own profile vs `PublicProfile` vs `MatchedProfile`).
- Do not put secrets in remote app-config.

---

## 10. Known pitfalls (do not reintroduce)

- Adding a `babel.config.js` with `presets: ['babel-preset-expo']` → `Cannot find module 'babel-preset-expo'` (nested dependency). Keep no custom babel config.
- `FlashList` v2 has no `estimatedItemSize` prop (that's v1). Removing it fixed the type error.
- Typing `useNavigation<NativeStackNavigationProp<AppStackParamList>>()` then `navigation.navigate(unionScreen)` fails overloads — cast the union argument (`navigate(screen as never)`) or branch explicitly for `'MainTabs'`.
- `Tab.Navigator` `tabBarBadge` accepts number|string only when defined — pass `undefined` for zero.
- `AppInput` interface must **not** `Omit<TextInputProps,'style'>` if you need `multiline` height styling — keep `style` available.
- API modules return `res.data` from `apiRequest` — don't double-unwrap `data.data`.
- Chat messages arrive **newest-first** from the backend — render with `inverted` FlatList; `useMessages` pagination appends older pages at the end.
- `imageUrl()` in `src/utils/imageUrl.ts` must be used for every backend image URL — some endpoints return raw object keys, which it maps to `/static/…` on the API host for local dev.
- Do not shadow React component names or import `View`/`Pressable` pieces you removed from a file — keep react-native imports complete (e.g. `Pressable`, `View`) or TS fails on usage.
- Env values used in code must be `EXPO_PUBLIC_*` (inlined) or come from `app.json` `extra` — plain `process.env.X` is not bundled.

---

## 11. Adding a new feature — checklist

1. Inspect the backend router + schema first (`app/api/v1/*`, `app/schemas/*`). Confirm no existing endpoint already provides it.
2. Add/update types in `src/types/models.ts` / `enums.ts` (mirror backend).
3. Add the API module function in `src/api/<domain>.ts` using `apiRequest` (returns `res.data`).
4. Add query keys + hooks in `src/query/keys.ts` and `src/features/<feature>/hooks.ts`.
5. Add the screen in `src/features/<feature>/` using the component library + `useTheme()` + `useRemoteConfig()`.
6. Register the screen in `src/navigation/AppNavigator.tsx` and type params in `navigation/types.ts`.
7. Add loading/empty/error states and pagination where data can grow.
8. Gate premium features by backend state/errors, not local assumptions.
9. Verify: `npm run typecheck`, `npx expo-doctor`, `npx expo export --platform android`.

---

## 12. Testing conventions

- No automated test runner is configured yet in `mobile/`. Do not claim tests passed unless actually executed.
- If adding tests, follow the backend pattern: meaningful behavior tests, never weaken existing checks, and isolate per test.
- Manual verification commands that are actually run and passing: `npm run typecheck` (clean), `npx expo-doctor` (20/20), `npx expo export --platform android` (bundles).

---

## 13. Definition of done

- `npm run typecheck` → clean.
- `npx expo-doctor` → no issues.
- `npx expo export --platform android` → bundles successfully.
- Backend contracts used as-is; no fabricated API responses; no secrets committed.
- No backend business rules duplicated; authorization/subscription/verification/privacy always read from the backend.
- Remote branding/theme/pricing used instead of hard-coded values.

---

## 14. AI Agent Operating Rules

- The backend (`../AGENTS.md`, `../docs/architecture.md`) and this file are the sources of truth; the task prompt is the UX/feature direction.
- Inspect existing code before writing new files; reuse existing components, hooks and API modules.
- Do not rewrite established architecture (framework, navigation style, state approach, component library) without explicit request.
- Keep changes focused; work in small, verifiable increments; validate after every change.
- If a requirement is ambiguous or conflicts with backend authority, choose the most conservative behavior, document the assumption, and call out the conflict before implementing.
- When reporting completed work, state exactly which validation commands were run and their results. Never claim a command passed unless it actually ran.
