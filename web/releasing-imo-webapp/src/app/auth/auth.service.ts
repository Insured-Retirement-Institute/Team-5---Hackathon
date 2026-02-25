import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

export type UserRole = 'agent' | 'imo';

export interface LoggedInUser {
  username: string;
  role: UserRole;
  imoFein: string;
}

/** Demo-only: hardcoded credentials. Do not use in production. */
const DEMO_USERS: ReadonlyArray<{ username: string; password: string; role: UserRole; imoFein: string }> = [
  { username: 'agent', password: 'password', role: 'agent', imoFein: '12-3456789' },
  { username: 'ImoAdmin', password: 'password', role: 'imo', imoFein: '12-3456789' },
];

const STORAGE_KEY = 'releasing-imo-webapp_logged_in_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly router = inject(Router);

  private readonly currentUserSignal = signal<LoggedInUser | null>(this.restoreUser());

  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly isLoggedIn = computed(() => this.currentUserSignal() !== null);

  private restoreUser(): LoggedInUser | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const user = JSON.parse(raw) as LoggedInUser;
      if (user?.username && user?.imoFein && (user.role === 'agent' || user.role === 'imo')) {
        return user;
      }
    } catch {
      // ignore invalid or missing storage
    }
    return null;
  }

  login(username: string, password: string): LoggedInUser | null {
    const normalizedUsername = username.trim();
    const user = DEMO_USERS.find(
      (u) => u.username === normalizedUsername && u.password === password
    );
    if (!user) {
      return null;
    }
    const loggedIn: LoggedInUser = { username: user.username, role: user.role, imoFein: user.imoFein };
    this.currentUserSignal.set(loggedIn);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedIn));
    return loggedIn;
  }

  logout(): void {
    localStorage.removeItem(STORAGE_KEY);
    this.currentUserSignal.set(null);
    this.router.navigate(['/login']);
  }
}
