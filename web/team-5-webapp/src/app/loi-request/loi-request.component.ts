import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, TransferCreateRequest, ImoInfo, allImos } from '../api/api.service';

interface ImoOption extends ImoInfo {
  label: string;
}

@Component({
  selector: 'app-loi-request',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './loi-request.component.html',
  styleUrl: './loi-request.component.scss',
})
export class LoiRequestComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);
  protected readonly submitSuccess = signal(false);

  releasingImoOptions: ImoOption[] = [];

  private readonly receivingImo: ImoInfo = {
    fein: '22-2222222',
    name: 'Current IMO',
  };

  protected readonly form = this.fb.nonNullable.group({
    agentFirstName: ['', Validators.required],
    agentLastName: ['', Validators.required],
    agentNpn: ['', Validators.required],
    releasingImo: ['', Validators.required],
    effectiveDate: ['', Validators.required],
  });

  ngOnInit(): void {
    this.releasingImoOptions = allImos.map((imo) => ({ ...imo, label: imo.name }));
  }

  protected onSubmit(): void {
    const { agentFirstName, agentLastName, agentNpn, releasingImo, effectiveDate } =
      this.form.getRawValue();

    const selectedImo = this.releasingImoOptions.find((o) => o.fein === releasingImo);
    if (!selectedImo) return;

    const request: TransferCreateRequest = {
      agent: { npn: agentNpn, firstName: agentFirstName, lastName: agentLastName },
      releasingImo: { fein: selectedImo.fein, name: selectedImo.name },
      receivingImo: this.receivingImo,
      effectiveDate,
      consent: { agentAttestation: true, eSignatureRef: '1234567890' },
    };

    this.submitting.set(true);
    this.submitError.set(null);
    this.submitSuccess.set(false);

    this.api.createTransfer(request).subscribe({
      next: () => {
        this.submitting.set(false);
        this.submitSuccess.set(true);
        this.form.reset();
      },
      error: (err) => {
        this.submitting.set(false);
        this.submitError.set(err?.error?.message ?? 'An unexpected error occurred.');
      },
    });
  }
}
