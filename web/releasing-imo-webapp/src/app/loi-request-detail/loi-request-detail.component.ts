import { ChangeDetectionStrategy, Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { switchMap, timer } from 'rxjs';
import { allCarriers, allImos, ApiService, LoiRequestStatusItem } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-loi-request-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './loi-request-detail.component.html',
  styleUrl: './loi-request-detail.component.scss',
})
export class LoiRequestDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);

  readonly groupItems = signal<LoiRequestStatusItem[] | null>(null);
  readonly loading = signal(true);

  ngOnInit(): void {
    const releasingFein = this.route.snapshot.queryParamMap.get('releasingFein');
    const npn = this.route.snapshot.queryParamMap.get('npn');

    if (!releasingFein || !npn) {
      this.loading.set(false);
      return;
    }

    timer(0, 2000).pipe(
      switchMap(() => this.api.getRequestStatuses(this.auth.currentUser()!.imoFein)),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (items) => {
        const filtered = items.filter(i => i.releasingFein === releasingFein && i.npn === npn);
        this.groupItems.set(filtered.length > 0 ? filtered : null);
        this.loading.set(false);
      },
      error: () => {
        this.groupItems.set(null);
        this.loading.set(false);
      },
    });
  }

  get agentName(): string {
    const first = this.groupItems()?.[0];
    if (!first) return '—';
    return `${first.agentFirstName} ${first.agentLastName}`.trim() || '—';
  }

  get npn(): string {
    return this.groupItems()?.[0]?.npn ?? '—';
  }

  get releasingImoName(): string {
    const fein = this.groupItems()?.[0]?.releasingFein;
    if (!fein) return '—';
    return allImos.find((imo) => imo.fein === fein)?.name ?? fein;
  }

  formatRequirementCode(code: string): string {
    return code.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  formatStatus(status: string): string {
    if (!status) return '—';
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
  }

  carrierName(carrierId: string): string {
    return allCarriers.find((c) => c.carrierId === carrierId)?.name ?? carrierId;
  }

  get supportingDoc(): { fileName: string; data: string } | null {
    const fein = this.groupItems()?.[0]?.releasingFein;
    const npn = this.groupItems()?.[0]?.npn;
    if (!fein || !npn) return null;
    const raw = localStorage.getItem(`supportingDoc_${fein}_${npn}`);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  downloadDoc(): void {
    const doc = this.supportingDoc;
    if (!doc) return;
    const link = document.createElement('a');
    link.href = doc.data;
    link.download = doc.fileName;
    link.click();
  }
}
