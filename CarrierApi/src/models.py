from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

@dataclass
class AgentRef:
    npn: str
    first_name: str
    last_name: str

@dataclass
class OrgRef:
    fein: str
    name: str

@dataclass
class Requirement:
    code: str
    status: str
    details: Optional[str] = None

@dataclass
class AuditEvent:
    event: str
    at: str
    from_state: Optional[str] = None
    to: Optional[str] = None

@dataclass
class StatusSetRequest:
    receiving_fein: str
    releasing_fein: str
    carrier_id: str
    status: str
    npn: str

@dataclass
class StatusRecord:
    receiving_fein: str
    releasing_fein: str
    carrier_id: str
    status: str
    npn: str

@dataclass
class Transfer:
    id: str
    state: str
    agent: AgentRef
    releasing_imo: OrgRef
    receiving_imo: OrgRef
    effective_date: str
    reasons: List[str] = None
    requirements: List[Requirement] = None
    audit: List[AuditEvent] = None

@dataclass
class TransferSummary:
    id: str
    state: str
    agent: AgentRef
    effective_date: str