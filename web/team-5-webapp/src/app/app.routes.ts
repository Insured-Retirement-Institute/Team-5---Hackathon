import { Routes } from '@angular/router';
import { agentGuard, authGuard, imoGuard, loginRedirectGuard } from './auth/guards';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login.component').then((m) => m.LoginComponent),
    canActivate: [loginRedirectGuard],
  },
  {
    path: 'book-of-business',
    loadComponent: () =>
      import('./book-of-business/book-of-business.component').then((m) => m.BookOfBusinessComponent),
    canActivate: [authGuard],
  },
  {
    path: 'loi-requests',
    loadComponent: () =>
      import('./loi-requests/loi-requests.component').then((m) => m.LoiRequestsComponent),
    canActivate: [authGuard, imoGuard],
  },
  {
    path: 'loi-requests/details',
    loadComponent: () =>
      import('./loi-request-detail/loi-request-detail.component').then((m) => m.LoiRequestDetailComponent),
    canActivate: [authGuard, imoGuard],
  },
  {
    path: 'loi-request',
    loadComponent: () =>
      import('./loi-request/loi-request.component').then((m) => m.LoiRequestComponent),
    canActivate: [authGuard, imoGuard],
  },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: 'login' },
];
