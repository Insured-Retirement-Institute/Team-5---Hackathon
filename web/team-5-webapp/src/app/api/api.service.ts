import { HttpClient, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

const BASE_URL = 'https://21yem0s5jl.execute-api.us-east-1.amazonaws.com/prod';

export interface TransferAgent {
  npn: string;
  firstName: string;
  lastName: string;
}

export interface ImoInfo {
  fein: string;
  name: string;
}

export interface CarrierInfo {
  carrierId: string;
  name: string;
}

export interface TransferCreateRequest {
  agent: TransferAgent;
  releasingImo: ImoInfo;
  receivingImo: ImoInfo;
  effectiveDate: string;
  consent: { agentAttestation: boolean; eSignatureRef: string } | null;
}

export interface LoiRequestStatusItem {
  ReceivingFein: string;
  ReleasingFein: string;
  npn: string;
  status: string;
  carrierId: string;
  agentFirstName: string;
  agentLastName: string;
}

export const allImos: ImoInfo[] = [
    { fein: '12-3456789', name: 'Past IMO' },
    { fein: '55-1234567', name: 'Summit IMO' },
];

export const allCarriers: CarrierInfo[] = [
  { carrierId: 'carrier_001', name: 'Carrier 1' },
  { carrierId: 'carrier_002', name: 'Carrier 2' },
];


@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  createTransfer(request: TransferCreateRequest, idempotencyKey?: string): Observable<unknown> {
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (idempotencyKey) {
      headers = headers.set('Idempotency-Key', idempotencyKey);
    }
    return this.http.post(`${BASE_URL}/ats/transfers`, request, { headers });
  }

  getAtsStatus(receivingFein: string): Observable<LoiRequestStatusItem[]> {
    return this.http.get<LoiRequestStatusItem[]>(`${BASE_URL}/ats/status/${encodeURIComponent(receivingFein)}`);
  }
}
