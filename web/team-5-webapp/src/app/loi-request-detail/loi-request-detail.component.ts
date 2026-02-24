import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { allCarriers, allImos, LoiRequestStatusItem } from '../api/api.service';

@Component({
  selector: 'app-loi-request-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './loi-request-detail.component.html',
  styleUrl: './loi-request-detail.component.scss',
})
export class LoiRequestDetailComponent implements OnInit {
  private readonly router = inject(Router);

  groupItems: LoiRequestStatusItem[] | null = null;

  ngOnInit(): void {
    const nav = this.router.lastSuccessfulNavigation();
    const state = nav?.extras?.state;
    this.groupItems = (state && state['groupItems']) ?? null;
  }

  get agentName(): string {
    const first = this.groupItems?.[0];
    if (!first) return '—';
    return `${first.agentFirstName} ${first.agentLastName}`.trim() || '—';
  }

  get npn(): string {
    return this.groupItems?.[0]?.npn ?? '—';
  }

  get releasingImoName(): string {
    const fein = this.groupItems?.[0]?.ReleasingFein;
    if (!fein) return '—';
    return allImos.find((imo) => imo.fein === fein)?.name ?? fein;
  }

  formatStatus(status: string): string {
    if (!status) return '—';
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
  }

  carrierName(carrierId: string): string {
    return allCarriers.find((c) => c.carrierId === carrierId)?.name ?? carrierId;
  }
}
