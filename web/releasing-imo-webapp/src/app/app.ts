import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './auth/auth.service';
import { TopMenuComponent } from './layout/top-menu/top-menu.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TopMenuComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly auth = inject(AuthService);
  visitorCount = Math.floor(Math.random() * 900) + 100;
}
