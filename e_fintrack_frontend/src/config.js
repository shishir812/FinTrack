function normalizeApiUrl(value) {
  const baseUrl = (value || 'http://127.0.0.1:8000/api').replace(/\/+$/, '');
  return baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`;
}

export const API_URL = normalizeApiUrl(import.meta.env.VITE_API_URL);

export const ROLE_OPTIONS = [
  { label: 'Admin', value: 'ADMIN' },
  { label: 'Bank employee', value: 'EMPLOYEE' },
  { label: 'Member', value: 'CUSTOMER' },
];

export const ROLE_HELP = {
  ADMIN: 'Use an administrator account to approve transactions, approve loans, and manage account status.',
  EMPLOYEE: 'Use a bank employee account to issue loans and handle bank-side operations.',
  CUSTOMER: 'Use a member account to transfer money, manage beneficiaries, and repay loans.',
};

export const DEMO_ACCOUNTS = [
  { label: 'Admin', role: 'ADMIN', username: 'admin', password: 'admin123' },
  { label: 'Employee', role: 'EMPLOYEE', username: 'employee', password: 'employee123' },
  { label: 'Member', role: 'CUSTOMER', username: 'member', password: 'member123' },
];

export const ROLE = {
  ADMIN: 'ADMIN',
  EMPLOYEE: 'EMPLOYEE',
  CUSTOMER: 'CUSTOMER',
};
