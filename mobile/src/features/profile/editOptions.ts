/** Edit-profile field option sets (see src/api/lookups.ts for full lists). */
import {
  BODY_TYPE_OPTIONS,
  CASTES,
  CITIES,
  COMPLEXION_OPTIONS,
  COUNTRIES,
  DIET_OPTIONS,
  DRINKING_OPTIONS,
  EMPLOYMENT_STATUS_OPTIONS,
  FAMILY_TYPE_OPTIONS,
  FAMILY_VALUES_OPTIONS,
  INTENT_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  MOTHER_TONGUES,
  OCCUPATIONS,
  PHYSICAL_STATUS_OPTIONS,
  RELIGIONS,
  SMOKING_OPTIONS,
  STATES,
} from '../../api/lookups';

export const GENDER_OPTIONS = [
  { value: 'MALE', label: 'Male' },
  { value: 'FEMALE', label: 'Female' },
  { value: 'OTHER', label: 'Other' },
];

export const HEIGHT_OPTIONS = Array.from({ length: 121 }, (_, i) => 100 + i).map((cm) => ({
  value: String(cm),
  label: `${Math.floor(cm / 2.54 / 12)}' ${Math.round((cm / 2.54) % 12)}" (${cm} cm)`,
}));

export {
  BODY_TYPE_OPTIONS,
  CASTES,
  CITIES,
  COMPLEXION_OPTIONS,
  COUNTRIES,
  DIET_OPTIONS,
  DRINKING_OPTIONS,
  EMPLOYMENT_STATUS_OPTIONS,
  FAMILY_TYPE_OPTIONS,
  FAMILY_VALUES_OPTIONS,
  INTENT_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  MOTHER_TONGUES,
  OCCUPATIONS,
  PHYSICAL_STATUS_OPTIONS,
  RELIGIONS,
  SMOKING_OPTIONS,
  STATES,
};
