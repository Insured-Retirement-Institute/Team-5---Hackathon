import { HttpClient, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

const BASE_URL = 'https://21yem0s5jl.execute-api.us-east-1.amazonaws.com/prod/ats/v1';

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

export interface Contract {
  fein: string;
  contractNumber: string;
  npn: string;
  carrierId: string;
  contractType: string;
  contractValue: string;
  issueDate: string;
  agentFirstName: string;
  agentLastName: string;
  id: string;
}

export interface TransferCreateRequest {
  agent: TransferAgent;
  releasingImo: ImoInfo;
  receivingImo: ImoInfo;
  effectiveDate: string;
  consent: { agentAttestation: boolean; eSignatureRef: string } | null;
}

export interface TransferRecord {
  id: string;
  agent: TransferAgent;
  releasingImo: ImoInfo;
  receivingImo: ImoInfo;
  effectiveDate: string;
  consent: { agentAttestation: boolean; eSignatureRef: string } | null;
}

export interface LoiRequestRequirement {
  code: string;
  status: string;
  details: string;
}

export interface LoiRequestStatusItem {
  receivingFein: string;
  releasingFein: string;
  npn: string;
  status: string;
  carrierId: string;
  agentFirstName: string;
  agentLastName: string;
  requirements: LoiRequestRequirement[];
}

export const allImos: ImoInfo[] = [
    { fein: '12-3456789', name: 'Initrode IMO' },
    { fein: '98-7654321', name: 'Advisors Excel' },
    { fein: '55-1234567', name: 'Some Other IMO' },
];

export const allCarriers: CarrierInfo[] = [
  { carrierId: 'carrier_001', name: 'Carrier 1' },
  { carrierId: 'carrier_002', name: 'Carrier 2' },
  { carrierId: 'allianz', name: 'Allianz' },
  { carrierId: 'american-equity', name: 'American Equity' },
];


@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  createTransfer(request: TransferCreateRequest, idempotencyKey?: string): Observable<unknown> {
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (idempotencyKey) {
      headers = headers.set('Idempotency-Key', idempotencyKey);
    }
    return this.http.post(`${BASE_URL}/transfers`, request, { headers });
  }

  getRequestStatuses(receivingFein: string): Observable<LoiRequestStatusItem[]> {
    return this.http.get<LoiRequestStatusItem[]>(`${BASE_URL}/status/${encodeURIComponent(receivingFein)}`);
  }

  getIncomingRequests(releasingFein: string): Observable<TransferRecord[]> {
    return this.http.get<TransferRecord[]>(`${BASE_URL}/transfers/${encodeURIComponent(releasingFein)}`);
  }

  getContracts(fein: string): Observable<Contract[]> {
    return this.http.get<Contract[]>(`${BASE_URL}/contracts/${encodeURIComponent(fein)}`);
  }

  releaseTransfer(transferId: string): Observable<unknown> {
    return this.http.post(`${BASE_URL}/transfers/${encodeURIComponent(transferId)}/release`, {});
  }
}
