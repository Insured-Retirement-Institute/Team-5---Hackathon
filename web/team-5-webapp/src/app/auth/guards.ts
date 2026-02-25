import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Redirect to login if not logged in. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (auth.isLoggedIn()) {
    return true;
  }
  return inject(Router).createUrlTree(['/login']);
};

/** Allow only agent role; redirect others to IMO area. */
export const agentGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const user = auth.currentUser();
  if (user?.role === 'agent') {
    return true;
  }
  if (user?.role === 'imo') {
    return inject(Router).createUrlTree(['/imo']);
  }
  return inject(Router).createUrlTree(['/login']);
};

/** Allow only IMO role; redirect others to agent area. */
export const imoGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const user = auth.currentUser();
  if (user?.role === 'imo') {
    return true;
  }
  if (user?.role === 'agent') {
    return inject(Router).createUrlTree(['/agent']);
  }
  return inject(Router).createUrlTree(['/login']);
};

/** If already logged in, redirect to role-specific area. */
export const loginRedirectGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const user = auth.currentUser();
  if (!user) {
    return true;
  }
  const target = user.role === 'agent' ? '/agent' : '/imo';
  return inject(Router).createUrlTree([target]);
};
