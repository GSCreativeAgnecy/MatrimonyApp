/**
 * UI option sets for profile/filter forms.
 *
 * The backend stores these profile/preference fields as free-form strings and
 * exposes NO lookup endpoint for countries/states/religions/castes/occupations
 * today. These curated lists therefore represent common, valid choices for the
 * form UX. The backend remains the source of truth for stored values — the app
 * always sends the string value and never invents new enum contracts.
 *
 * (Backend follow-up: expose the `lookups` tables via a public endpoint.)
 */

export const RELIGIONS = [
  'Hindu',
  'Muslim',
  'Christian',
  'Sikh',
  'Jain',
  'Buddhist',
  'Parsi',
  'Jewish',
  'Spiritual',
  'No Religion',
];

export const CASTES = [
  'Brahmin',
  'Kshatriya',
  'Vaishya',
  'Shudra',
  'Rajput',
  'Jat',
  'Yadav',
  'Patel',
  'Reddy',
  'Naidu',
  'Iyengar',
  'Iyer',
  'Kayastha',
  'Maratha',
  'Sindhi',
  'Bania',
  'Aggarwal',
  'Gupta',
  'Nair',
  'Vanniyar',
  'Gounder',
  'Vokkaliga',
  'Lingayat',
  'Rajbanshi',
  'Kurmi',
  'Other',
];

export const OCCUPATIONS = [
  'Software Engineer',
  'Engineer - Non IT',
  'Doctor',
  'Nurse',
  'Teacher / Professor',
  'Accountant',
  'Business Owner',
  'Entrepreneur',
  'Civil Services',
  'Defence / Armed Forces',
  'Lawyer',
  'Banking Professional',
  'Marketing Professional',
  'Manager',
  'Consultant',
  'Architect',
  'Designer',
  'Scientist',
  'Research',
  'Media / Entertainment',
  'Admin Professional',
  'Airline Professional',
  'Civil Engineer',
  'Mechanical Engineer',
  'Electrical Engineer',
  'Government Officer',
  'Homemaker',
  'Not Working',
  'Retired',
  'Student',
  'Other',
];

export const COUNTRIES = [
  'India',
  'United States',
  'United Kingdom',
  'Canada',
  'Australia',
  'New Zealand',
  'United Arab Emirates',
  'Saudi Arabia',
  'Kuwait',
  'Qatar',
  'Bahrain',
  'Oman',
  'Singapore',
  'Malaysia',
  'Germany',
  'Netherlands',
  'France',
  'Switzerland',
  'Japan',
  'South Africa',
  'Other',
];

export const CITIES = [
  'Mumbai',
  'Delhi',
  'Bengaluru',
  'Hyderabad',
  'Ahmedabad',
  'Chennai',
  'Kolkata',
  'Pune',
  'Jaipur',
  'Surat',
  'Lucknow',
  'Kanpur',
  'Nagpur',
  'Indore',
  'Thane',
  'Bhopal',
  'Visakhapatnam',
  'Patna',
  'Vadodara',
  'Ghaziabad',
  'Ludhiana',
  'Agra',
  'Nashik',
  'Faridabad',
  'Meerut',
  'Rajkot',
  'Varanasi',
  'Srinagar',
  'Aurangabad',
  'Coimbatore',
  'Kochi',
  'Thiruvananthapuram',
  'Chandigarh',
  'Amritsar',
  'Gurugram',
  'Noida',
  'Dehradun',
  'Guwahati',
  'Other',
];

export const STATES = [
  'Andhra Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Delhi',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Tamil Nadu',
  'Telangana',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
];

export const MOTHER_TONGUES = [
  'Hindi',
  'Bengali',
  'Marathi',
  'Telugu',
  'Tamil',
  'Gujarati',
  'Urdu',
  'Kannada',
  'Odia',
  'Malayalam',
  'Punjabi',
  'Assamese',
  'Bhojpuri',
  'Rajasthani',
  'English',
  'Other',
];

export const MARITAL_STATUS_OPTIONS = [
  { value: 'NEVER_MARRIED', label: 'Never Married' },
  { value: 'DIVORCED', label: 'Divorced' },
  { value: 'WIDOWED', label: 'Widowed' },
  { value: 'AWAITING_DIVORCE', label: 'Awaiting Divorce' },
];

export const DIET_OPTIONS = [
  { value: 'VEGETARIAN', label: 'Vegetarian' },
  { value: 'NON_VEGETARIAN', label: 'Non-Vegetarian' },
  { value: 'EGGITARIAN', label: 'Eggetarian' },
  { value: 'JAIN', label: 'Jain' },
  { value: 'VEGAN', label: 'Vegan' },
];

export const DRINKING_OPTIONS = [
  { value: 'NEVER', label: 'No' },
  { value: 'OCCASIONALLY', label: 'Occasionally' },
  { value: 'REGULARLY', label: 'Regularly' },
  { value: 'PREFER_NOT_TO_SAY', label: "Don't want to specify" },
];

export const SMOKING_OPTIONS = [
  { value: 'NEVER', label: 'No' },
  { value: 'OCCASIONALLY', label: 'Occasionally' },
  { value: 'REGULARLY', label: 'Regularly' },
  { value: 'PREFER_NOT_TO_SAY', label: "Don't want to specify" },
];

export const BODY_TYPE_OPTIONS = [
  { value: 'SLIM', label: 'Slim' },
  { value: 'AVERAGE', label: 'Average' },
  { value: 'ATHLETIC', label: 'Athletic' },
  { value: 'HEAVY', label: 'Heavy' },
];

export const COMPLEXION_OPTIONS = [
  { value: 'VERY_FAIR', label: 'Very Fair' },
  { value: 'FAIR', label: 'Fair' },
  { value: 'WHEATISH', label: 'Wheatish' },
  { value: 'MIDDLE_BROWN', label: 'Middle Brown' },
  { value: 'DARK', label: 'Dark' },
];

export const EMPLOYMENT_STATUS_OPTIONS = [
  { value: 'EMPLOYED', label: 'Employed' },
  { value: 'SELF_EMPLOYED', label: 'Self Employed' },
  { value: 'BUSINESS_OWNER', label: 'Business Owner' },
  { value: 'STUDENT', label: 'Student' },
  { value: 'NOT_WORKING', label: 'Not Working' },
  { value: 'RETIRED', label: 'Retired' },
  { value: 'HOMEMAKER', label: 'Homemaker' },
];

export const INTENT_OPTIONS = [
  { value: 'MARRIAGE', label: 'Marriage' },
  { value: 'FRIENDSHIP', label: 'Friendship' },
  { value: 'DATE', label: 'Date' },
  { value: 'NOT_SURE', label: 'Not Sure' },
];

export const PHYSICAL_STATUS_OPTIONS = [
  { value: 'NORMAL', label: 'Normal' },
  { value: 'PHYSICALLY_CHALLENGED', label: 'Physically Challenged' },
];

export const PROFILE_CREATED_BY_OPTIONS = [
  { value: 'SELF', label: 'Myself' },
  { value: 'PARENT', label: 'Parent' },
  { value: 'GUARDIAN', label: 'Guardian' },
  { value: 'RELATIVE', label: 'Relative' },
  { value: 'FRIEND', label: 'Friend' },
  { value: 'PROFILE_SERVICE', label: 'Profile Service' },
];

export const FAMILY_TYPE_OPTIONS = [
  { value: 'JOINT', label: 'Joint Family' },
  { value: 'NUCLEAR', label: 'Nuclear Family' },
  { value: 'EXTENDED', label: 'Extended Family' },
];

export const FAMILY_VALUES_OPTIONS = [
  { value: 'TRADITIONAL', label: 'Traditional' },
  { value: 'MODERATE', label: 'Moderate' },
  { value: 'LIBERAL', label: 'Liberal' },
  { value: 'ORTHODOX', label: 'Orthodox' },
];

export const RASHI_OPTIONS = [
  { value: 'MESHA', label: 'Mesha (Aries)' },
  { value: 'VRISHABHA', label: 'Vrishabha (Taurus)' },
  { value: 'MITHUNA', label: 'Mithuna (Gemini)' },
  { value: 'KARKA', label: 'Karka (Cancer)' },
  { value: 'SIMHA', label: 'Simha (Leo)' },
  { value: 'KANYA', label: 'Kanya (Virgo)' },
  { value: 'TULA', label: 'Tula (Libra)' },
  { value: 'VRISHCHIKA', label: 'Vrishchika (Scorpio)' },
  { value: 'DHANU', label: 'Dhanu (Sagittarius)' },
  { value: 'MAKARA', label: 'Makara (Capricorn)' },
  { value: 'KUMBHA', label: 'Kumbha (Aquarius)' },
  { value: 'MEENA', label: 'Meena (Pisces)' },
];

export const DOSHAM_OPTIONS = [
  { value: 'NONE', label: 'No Dosham' },
  { value: 'MANGAL', label: 'Mangal Dosham' },
  { value: 'PARTHIV', label: 'Parthiv Dosham' },
  { value: 'OTHER', label: 'Other' },
];
