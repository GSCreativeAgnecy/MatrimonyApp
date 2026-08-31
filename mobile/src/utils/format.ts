/** Formatting helpers shared across screens. */

export function initials(firstName?: string | null, lastName?: string | null): string {
  const first = (firstName || '')[0] || '';
  const last = (lastName || '')[0] || '';
  const value = `${first}${last}`.toUpperCase();
  return value || '?';
}

export function fullName(firstName?: string | null, lastName?: string | null): string {
  return [firstName, lastName].filter(Boolean).join(' ') || 'Ardhang Member';
}

/** Rough profile completeness from the required backend profile fields. */
const REQUIRED_FIELDS: Array<keyof Record<string, unknown>> = [
  'first_name',
  'date_of_birth',
  'gender',
  'religion',
  'caste',
  'education',
  'occupation',
  'city',
  'country',
];

export function profileCompleteness(profile: Record<string, unknown> | null | undefined): number {
  if (!profile) {
    return 0;
  }
  const filled = REQUIRED_FIELDS.filter((f) => {
    const v = profile[f];
    return v !== null && v !== undefined && v !== '';
  }).length;
  return Math.round((filled / REQUIRED_FIELDS.length) * 100);
}

/** Height in cm → "5' 7\" (170 cm)". */
export function formatHeight(cm: number | null | undefined): string {
  if (!cm) {
    return '—';
  }
  const totalInches = Math.round(cm / 2.54);
  const ft = Math.floor(totalInches / 12);
  const inch = totalInches % 12;
  return `${ft}' ${inch}" (${cm} cm)`;
}

/** Annual income to compact INR text. */
export function formatIncome(amount: number | null | undefined, currency: string | null | undefined = 'INR'): string {
  if (amount === null || amount === undefined) {
    return 'Not specified';
  }
  const symbol = currency === 'INR' ? '₹' : `${currency} `;
  if (amount >= 1_000_000) {
    return `${symbol}${(amount / 1_000_000).toLocaleString('en-IN')}L+`;
  }
  if (amount >= 100_000) {
    return `${symbol}${(amount / 100_000).toLocaleString('en-IN')}L`;
  }
  if (amount >= 1_000) {
    return `${symbol}${(amount / 1_000).toLocaleString('en-IN')}k`;
  }
  return `${symbol}${amount}`;
}

export function formatPrice(amount: number | null | undefined, currency = 'INR'): string {
  if (amount === null || amount === undefined) {
    return '—';
  }
  const symbol = currency === 'INR' ? '₹' : `${currency} `;
  return `${symbol}${Number(amount).toLocaleString('en-IN')}`;
}

/** Human relative time, e.g. "10m", "2h", "3d", "Just now". */
export function relativeTime(value: string | null | undefined): string {
  if (!value) {
    return '';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  const diffMs = Date.now() - date.getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) {
    return 'Just now';
  }
  if (mins < 60) {
    return `${mins}m`;
  }
  const hours = Math.floor(mins / 60);
  if (hours < 24) {
    return `${hours}h`;
  }
  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `${days}d`;
  }
  return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

export function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 17) return 'Good Afternoon';
  return 'Good Evening';
}

/** Pretty label for a marital status enum. */
export function maritalStatusLabel(value: string | null | undefined): string {
  switch (value) {
    case 'NEVER_MARRIED':
      return 'Never Married';
    case 'DIVORCED':
      return 'Divorced';
    case 'WIDOWED':
      return 'Widowed';
    case 'AWAITING_DIVORCE':
      return 'Awaiting Divorce';
    default:
      return 'Not specified';
  }
}

export function titleCase(value: string | null | undefined): string {
  if (!value) return '—';
  return value
    .toLowerCase()
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}
