import { CurrencyPipe, DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from '@angular/core';
import { allCarriers, ApiService, Contract } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

export interface ContractRow {
  id: string;
  fein: string;
  contractNumber: string;
  agentName: string;
  npn: string;
  carrierName: string;
  contractType: string;
  contractValue: number;
  issueDate: string;
}

type SortableColumn = 'contractNumber' | 'agentName' | 'npn' | 'carrierName' | 'contractType' | 'contractValue' | 'issueDate';
type SortDirection = 'asc' | 'desc';

const NUMERIC_COLUMNS: ReadonlySet<SortableColumn> = new Set(['contractValue']);

@Component({
  selector: 'app-book-of-business',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './book-of-business.component.html',
  styleUrl: './book-of-business.component.scss',
})
export class BookOfBusinessComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  readonly rows = signal<ContractRow[]>([]);
  readonly loading = signal(true);

  readonly sortColumn = signal<SortableColumn>('contractNumber');
  readonly sortDirection = signal<SortDirection>('asc');

  readonly sortedRows = computed(() => {
    const data = [...this.rows()];
    const col = this.sortColumn();
    const dir = this.sortDirection();
    return data.sort((a, b) => {
      let cmp: number;
      if (NUMERIC_COLUMNS.has(col)) {
        cmp = (a[col] as number) - (b[col] as number);
      } else {
        cmp = String(a[col]).localeCompare(String(b[col]));
      }
      return dir === 'asc' ? cmp : -cmp;
    });
  });

  ngOnInit(): void {
    const fein = this.auth.currentUser()?.imoFein;
    if (!fein) {
      this.loading.set(false);
      return;
    }

    this.api.getContracts(fein).subscribe({
      next: (contracts) => {
        this.rows.set(contracts.map(this.toRow));
        this.loading.set(false);
      },
      error: () => {
        this.rows.set([]);
        this.loading.set(false);
      },
    });
  }

  toggleSort(column: SortableColumn): void {
    if (this.sortColumn() === column) {
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortColumn.set(column);
      this.sortDirection.set('asc');
    }
  }

  private toRow(contract: Contract): ContractRow {
    const carrier = allCarriers.find((c) => c.carrierId === contract.carrierId);
    return {
      id: contract.id,
      fein: contract.fein,
      contractNumber: contract.contractNumber,
      agentName: `${contract.agentFirstName} ${contract.agentLastName}`.trim(),
      npn: contract.npn,
      carrierName: carrier?.name ?? contract.carrierId,
      contractType: contract.contractType,
      contractValue: Number(contract.contractValue),
      issueDate: contract.issueDate,
    };
  }
}
