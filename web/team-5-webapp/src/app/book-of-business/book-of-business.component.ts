import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-book-of-business',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './book-of-business.component.html',
  styleUrl: './book-of-business.component.scss',
})
export class BookOfBusinessComponent {}
