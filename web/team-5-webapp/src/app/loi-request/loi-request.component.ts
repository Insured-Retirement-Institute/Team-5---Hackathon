import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, TransferCreateRequest, ImoInfo, allImos } from '../api/api.service';
import { AuthService } from '../auth/auth.service';

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
  private readonly auth = inject(AuthService);

  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);
  protected readonly submitSuccess = signal(false);
  protected readonly selectedFileName = signal<string | null>(null);

  private selectedFileData: string | null = null;

  releasingImoOptions: ImoOption[] = [];

  private readonly receivingImo: ImoInfo = {
    fein: this.auth.currentUser()!.imoFein,
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

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.selectedFileName.set(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      this.selectedFileData = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  protected removeFile(event: Event): void {
    event.stopPropagation();
    this.selectedFileName.set(null);
    this.selectedFileData = null;
  }

  private storeDocInLocalStorage(releasingFein: string, npn: string): void {
    if (!this.selectedFileData) return;
    const key = `supportingDoc_${releasingFein}_${npn}`;
    try {
      localStorage.setItem(key, JSON.stringify({
        fileName: this.selectedFileName(),
        data: this.selectedFileData,
        storedAt: new Date().toISOString(),
      }));
    } catch {
      console.warn('Failed to store document in localStorage (likely exceeds quota).');
    }
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
        this.storeDocInLocalStorage(selectedImo.fein, agentNpn);
        this.submitting.set(false);
        this.submitSuccess.set(true);
        this.form.reset();
        this.selectedFileName.set(null);
        this.selectedFileData = null;
      },
      error: (err) => {
        this.submitting.set(false);
        this.submitError.set(err?.error?.message ?? 'An unexpected error occurred.');
      },
    });
  }
}
