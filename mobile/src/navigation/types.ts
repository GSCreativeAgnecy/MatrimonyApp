import { NavigatorScreenParams } from '@react-navigation/native';

export type AuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

export type MainTabsParamList = {
  ProfileTab: undefined;
  MatchesTab: undefined;
  ChatTab: undefined;
  AlertsTab: undefined;
  PremiumTab: undefined;
};

export type AppStackParamList = {
  MainTabs: NavigatorScreenParams<MainTabsParamList> | undefined;
  Dashboard: undefined;
  ProfileDetails: { userId: string };
  EditProfile: undefined;
  Photos: undefined;
  MatchFilters: undefined;
  ChatConversation: { conversationId: string; otherUserId: string; otherUserName?: string };
  HoroscopeMatch: undefined;
  Services: undefined;
  Settings: undefined;
  HelpSupport: undefined;
  Referral: undefined;
  More: undefined;
  JobVerification: undefined;
};

export type RootStackParamList = {
  Loading: undefined;
  Auth: NavigatorScreenParams<AuthStackParamList> | undefined;
  App: NavigatorScreenParams<AppStackParamList> | undefined;
};

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
