/** Client-side validation helpers. The backend remains authoritative. */

export function isEmailValid(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function isPhoneValid(phone: string): boolean {
  return /^[+]?[0-9]{8,15}$/.test(phone.trim());
}

export interface PasswordStrength {
  score: number; // 0..4
  label: string;
  checks: {
    length: boolean;
    upper: boolean;
    lower: boolean;
    digit: boolean;
    special: boolean;
  };
}

/**
 * Mirror of the backend password rule: at least 8 chars, one uppercase, one digit.
 * The strength meter scores additional criteria for UX only.
 */
export function passwordStrength(password: string): PasswordStrength {
  const checks = {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    digit: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };

  const passed = Object.values(checks).filter(Boolean).length;
  let score = 0;
  if (password.length === 0) {
    score = 0;
  } else if (passed <= 2) {
    score = 1;
  } else if (passed === 3) {
    score = 2;
  } else if (passed === 4) {
    score = 3;
  } else {
    score = 4;
  }

  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  return { score, label: labels[score], checks };
}

/** Minimum backend requirement: 8+ chars with at least one uppercase and one digit. */
export function isBackendValidPassword(password: string): boolean {
  return password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
}

export function isValidDateOfBirth(dob: string): boolean {
  const date = new Date(dob);
  if (Number.isNaN(date.getTime())) return false;
  const today = new Date();
  let age = today.getFullYear() - date.getFullYear();
  const m = today.getMonth() - date.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < date.getDate())) age -= 1;
  return age >= 18;
}
