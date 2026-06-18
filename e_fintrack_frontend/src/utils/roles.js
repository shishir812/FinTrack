import { ROLE } from '../config';

export function isAdminUser(user) {
  return user?.role === ROLE.ADMIN || user?.is_staff;
}

export function canManageLoans(user) {
  return isAdminUser(user) || user?.role === ROLE.EMPLOYEE;
}
