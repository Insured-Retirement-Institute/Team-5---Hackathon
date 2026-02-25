from copy import deepcopy

AGENTS = [
    {
        "id": "agt_1001",
        "npn": "17439285",
        "firstName": "Jordan",
        "lastName": "Miles",
        "currentImo": {
            "name": "Legacy IMO Group",
            "fein": "12-3456789",
        },
        "carriers": [
            {
                "carrierId": "carrier_001",
                "carrierName": "Northstar Life",
                "licensed": True,
                "requirements": {
                    "requiresReleaseLetter": True,
                    "requiresSignedTransferPacket": True,
                    "minimumDaysInCurrentHierarchy": 180,
                },
            },
            {
                "carrierId": "carrier_014",
                "carrierName": "Pioneer Financial",
                "licensed": True,
                "requirements": {
                    "requiresReleaseLetter": False,
                    "requiresSignedTransferPacket": True,
                    "minimumDaysInCurrentHierarchy": 90,
                },
            },
        ],
        "bookOfBusiness": [
            {
                "bookId": "bob_1001_A",
                "carrierId": "carrier_001",
                "policyCount": 42,
                "annualizedPremium": 1850000.00,
            },
            {
                "bookId": "bob_1001_B",
                "carrierId": "carrier_014",
                "policyCount": 17,
                "annualizedPremium": 540000.00,
            },
        ],
    },
    {
        "id": "agt_1002",
        "npn": "19384572",
        "firstName": "Avery",
        "lastName": "Chen",
        "currentImo": {
            "name": "Legacy IMO Group",
            "fein": "12-3456789",
        },
        "carriers": [
            {
                "carrierId": "carrier_003",
                "carrierName": "Blue Harbor",
                "licensed": True,
                "requirements": {
                    "requiresReleaseLetter": True,
                    "requiresSignedTransferPacket": False,
                    "minimumDaysInCurrentHierarchy": 120,
                },
            },
            {
                "carrierId": "carrier_009",
                "carrierName": "Summit Annuity",
                "licensed": True,
                "requirements": {
                    "requiresReleaseLetter": False,
                    "requiresSignedTransferPacket": True,
                    "minimumDaysInCurrentHierarchy": 60,
                },
            },
        ],
        "bookOfBusiness": [
            {
                "bookId": "bob_1002_A",
                "carrierId": "carrier_003",
                "policyCount": 23,
                "annualizedPremium": 950000.00,
            },
            {
                "bookId": "bob_1002_B",
                "carrierId": "carrier_009",
                "policyCount": 11,
                "annualizedPremium": 420000.00,
            },
        ],
    },
]


def list_agents(receiving_imo_fein: str | None = None):
    if not receiving_imo_fein:
        return deepcopy(AGENTS)

    return [
        deepcopy(agent)
        for agent in AGENTS
        if agent.get("currentImo", {}).get("fein") != receiving_imo_fein
    ]


def get_agent(agent_id: str):
    for agent in AGENTS:
        if agent["id"] == agent_id:
            return deepcopy(agent)
    return None
