import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { allImos, ApiService, LoiRequestStatusItem } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

export interface LoiRequestRow {
  agentName: string;
  npn: string;
  releasingImoName: string;
  status: 'Pending' | 'Completed' | 'Rejected' | 'Initiated';
  groupItems: LoiRequestStatusItem[];
}

@Component({
  selector: 'app-loi-requests',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './loi-requests.component.html',
  styleUrl: './loi-requests.component.scss',
})
export class LoiRequestsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  readonly rows = signal<LoiRequestRow[]>([]);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.api.getRequestStatuses(this.auth.currentUser()!.imoFein).subscribe({
      next: (items) => {
        this.rows.set(this.groupAndMapRows(items));
        this.loading.set(false);
      },
      error: () => {
        this.rows.set([]);
        this.loading.set(false);
      },
    });
  }

  navigateToDetail(row: LoiRequestRow): void {
    const first = row.groupItems[0];
    this.router.navigate(['/loi-requests/details'], {
      queryParams: { releasingFein: first.releasingFein, npn: first.npn },
    });
  }

  private groupAndMapRows(items: LoiRequestStatusItem[]): LoiRequestRow[] {
    const groupKey = (item: LoiRequestStatusItem) => `${item.releasingFein}|${item.npn}`;
    const groups = new Map<string, LoiRequestStatusItem[]>();
    for (const item of items) {
      const key = groupKey(item);
      const list = groups.get(key) ?? [];
      list.push(item);
      groups.set(key, list);
    }
    return Array.from(groups.entries()).map(([, groupItems]) => {
      const first = groupItems[0];
      const releasingImo = allImos.find((imo) => imo.fein === first.releasingFein);
      const isComplete = groupItems.every((i) => i.status === 'COMPLETED');
      const isRejected = groupItems.some((i) => i.status === 'REJECTED');
      const isInitiated = groupItems.some((i) => i.status === 'INITIATED');
      return {
        agentName: `${first.agentFirstName} ${first.agentLastName}`.trim(),
        npn: first.npn,
        releasingImoName: releasingImo?.name ?? first.releasingFein,
        status: isComplete ? 'Completed' : (isRejected ? 'Rejected' : (isInitiated ? 'Initiated' : 'Pending')),
        groupItems,
      } satisfies LoiRequestRow;
    });
  }
}
