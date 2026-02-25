import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { allImos, ApiService, LoiRequestStatusItem } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

export interface IncomingRequestRow {
  agentName: string;
  npn: string;
  receivingImoName: string;
  status: 'Pending' | 'Completed' | 'Rejected' | 'Initiated';
  groupItems: LoiRequestStatusItem[];
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
  private readonly auth = inject(AuthService);

  readonly rows = signal<IncomingRequestRow[]>([]);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.api.getIncomingRequests(this.auth.currentUser()!.imoFein).subscribe({
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

  private groupAndMapRows(items: LoiRequestStatusItem[]): IncomingRequestRow[] {
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
        receivingImoName: releasingImo?.name ?? first.releasingFein,
        status: isComplete ? 'Completed' : (isRejected ? 'Rejected' : (isInitiated ? 'Initiated' : 'Pending')),
        groupItems,
      } satisfies IncomingRequestRow;
    });
  }
}
