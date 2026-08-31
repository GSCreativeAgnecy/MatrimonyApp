/** Backend domain enums (mirrors app/db/enums.py). */
export type Gender = 'MALE' | 'FEMALE' | 'OTHER';
export type MaritalStatus = 'NEVER_MARRIED' | 'DIVORCED' | 'WIDOWED' | 'AWAITING_DIVORCE';
export type Diet = 'VEGETARIAN' | 'NON_VEGETARIAN' | 'EGGITARIAN' | 'JAIN' | 'VEGAN';
export type Drinking = 'NEVER' | 'OCCASIONALLY' | 'REGULARLY' | 'PREFER_NOT_TO_SAY';
export type Smoking = 'NEVER' | 'OCCASIONALLY' | 'REGULARLY' | 'PREFER_NOT_TO_SAY';
export type PhysicalStatus = 'NORMAL' | 'PHYSICALLY_CHALLENGED';
export type EmploymentStatus =
  | 'EMPLOYED'
  | 'SELF_EMPLOYED'
  | 'BUSINESS_OWNER'
  | 'STUDENT'
  | 'NOT_WORKING'
  | 'RETIRED'
  | 'HOMEMAKER';
export type Intent = 'MARRIAGE' | 'FRIENDSHIP' | 'DATE' | 'NOT_SURE';
export type ProfileCreatedBy = 'SELF' | 'PARENT' | 'GUARDIAN' | 'RELATIVE' | 'FRIEND' | 'PROFILE_SERVICE';
export type BodyType = 'SLIM' | 'AVERAGE' | 'ATHLETIC' | 'HEAVY';
export type Complexion = 'VERY_FAIR' | 'FAIR' | 'WHEATISH' | 'MIDDLE_BROWN' | 'DARK';
export type SwipeAction = 'LIKE' | 'PASS' | 'SUPER_LIKE';
export type PhotoVerificationStatus = 'UNVERIFIED' | 'PENDING' | 'VERIFIED' | 'REJECTED';
export type PhotoVisibility = 'PUBLIC' | 'PRIVATE';
export type PreferenceLevel = 'REQUIRED' | 'PREFERRED' | 'NO_PREFERENCE';
export type NotificationType =
  | 'NEW_MATCH'
  | 'NEW_MESSAGE'
  | 'NEW_LIKE'
  | 'PROFILE_VIEW'
  | 'VERIFICATION_COMPLETE'
  | 'SUBSCRIPTION_EXPIRING'
  | 'SYSTEM';
export type EmploymentType = 'LOCAL' | 'NRI';
export type FamilyType = 'JOINT' | 'NUCLEAR' | 'EXTENDED';
export type FamilyValues = 'TRADITIONAL' | 'MODERATE' | 'LIBERAL' | 'ORTHODOX';
export type AstrologyRashi =
  | 'MESHA'
  | 'VRISHABHA'
  | 'MITHUNA'
  | 'KARKA'
  | 'SIMHA'
  | 'KANYA'
  | 'TULA'
  | 'VRISHCHIKA'
  | 'DHANU'
  | 'MAKARA'
  | 'KUMBHA'
  | 'MEENA';
export type Dosham = 'NONE' | 'MANGAL' | 'PARTHIV' | 'OTHER';

/** Options the backend accepts for these free-form profile/preference fields. */
export interface OptionGroup {
  religions: string[];
  castes: string[];
  occupations: string[];
  countries: string[];
  states: Record<string, string[]>;
  cities: string[];
}
