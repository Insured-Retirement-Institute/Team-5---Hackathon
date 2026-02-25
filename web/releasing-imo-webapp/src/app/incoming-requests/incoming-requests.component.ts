import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService, TransferRecord } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

export interface IncomingRequestRow {
  agentName: string;
  npn: string;
  receivingFein: string;
  receivingImoName: string;
  effectiveDate: string;
}

@Component({
  selector: 'app-incoming-requests',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
  templateUrl: './incoming-requests.component.html',
  styleUrl: './incoming-requests.component.scss',
})
export class IncomingRequestsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  readonly rows = signal<IncomingRequestRow[]>([]);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.api.getIncomingRequests(this.auth.currentUser()!.imoFein).subscribe({
      next: (transfers) => {
        this.rows.set(this.mapRows(transfers));
        this.loading.set(false);
      },
      error: () => {
        this.rows.set([]);
        this.loading.set(false);
      },
    });
  }

  navigateToDetail(row: IncomingRequestRow): void {
    this.router.navigate(['/incoming-requests/details'], {
      queryParams: { npn: row.npn, receivingFein: row.receivingFein },
    });
  }

  private mapRows(transfers: TransferRecord[]): IncomingRequestRow[] {
    return transfers.map((t) => ({
      agentName: `${t.agent.firstName} ${t.agent.lastName}`.trim(),
      npn: t.agent.npn,
      receivingFein: t.receivingImo.fein,
      receivingImoName: t.receivingImo.name,
      effectiveDate: t.effectiveDate,
    }));
  }
}
