import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { allImos, ApiService, LoiRequestStatusItem } from '../api/api.service';

export interface LoiRequestRow {
  agentName: string;
  npn: string;
  releasingImoName: string;
  status: 'Pending' | 'Completed' | 'Rejected';
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

  readonly rows = signal<LoiRequestRow[]>([]);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.api.getAtsStatus('22-2222222').subscribe({
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
    this.router.navigate(['/loi-requests/details'], { state: { groupItems: row.groupItems } });
  }

  private groupAndMapRows(items: LoiRequestStatusItem[]): LoiRequestRow[] {
    const groupKey = (item: LoiRequestStatusItem) => `${item.ReleasingFein}|${item.npn}`;
    const groups = new Map<string, LoiRequestStatusItem[]>();
    for (const item of items) {
      const key = groupKey(item);
      const list = groups.get(key) ?? [];
      list.push(item);
      groups.set(key, list);
    }
    return Array.from(groups.entries()).map(([, groupItems]) => {
      const first = groupItems[0];
      const releasingImo = allImos.find((imo) => imo.fein === first.ReleasingFein);
      const isComplete = groupItems.every((i) => i.status === 'COMPLETED');
      const isRejected = groupItems.some((i) => i.status === 'REJECTED');
      return {
        agentName: `${first.agentFirstName} ${first.agentLastName}`.trim(),
        npn: first.npn,
        releasingImoName: releasingImo?.name ?? first.ReleasingFein,
        status: isComplete ? 'Completed' : (isRejected ? 'Rejected' : 'Pending'),
        groupItems,
      } satisfies LoiRequestRow;
    });
  }
}
