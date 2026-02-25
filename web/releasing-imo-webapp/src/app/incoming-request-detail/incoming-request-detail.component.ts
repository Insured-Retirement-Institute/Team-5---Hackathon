import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService, TransferRecord } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-incoming-request-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './incoming-request-detail.component.html',
  styleUrl: './incoming-request-detail.component.scss',
})
export class IncomingRequestDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  readonly transfer = signal<TransferRecord | null>(null);
  readonly loading = signal(true);
  readonly consented = signal(false);
  readonly releasing = signal(false);

  ngOnInit(): void {
    const npn = this.route.snapshot.queryParamMap.get('npn');
    const receivingFein = this.route.snapshot.queryParamMap.get('receivingFein');

    if (!npn || !receivingFein) {
      this.loading.set(false);
      return;
    }

    this.api.getIncomingRequests(this.auth.currentUser()!.imoFein).subscribe({
      next: (transfers) => {
        const match = transfers.find(
          (t) => t.agent.npn === npn && t.receivingImo.fein === receivingFein,
        );
        this.transfer.set(match ?? null);
        this.loading.set(false);
      },
      error: () => {
        this.transfer.set(null);
        this.loading.set(false);
      },
    });
  }

  get agentName(): string {
    const t = this.transfer();
    if (!t) return '—';
    return `${t.agent.firstName} ${t.agent.lastName}`.trim() || '—';
  }

  get receivingImoName(): string {
    return this.transfer()?.receivingImo.name ?? '—';
  }

  toggleConsent(): void {
    this.consented.update((v) => !v);
  }

  release(): void {
    const t = this.transfer();
    if (!t || this.releasing()) return;

    this.releasing.set(true);
    this.api.releaseTransfer(t.id).subscribe({
      next: () => {
        this.router.navigate(['/incoming-requests']);
      },
      error: () => {
        this.releasing.set(false);
      },
    });
  }
}
