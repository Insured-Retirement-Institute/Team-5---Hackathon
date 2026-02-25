from copy import deepcopy

AGENTS = [
    {
        "npn": "111",
        "firstName": "Bob",
        "lastName": "Slydell",
        "currentImo": {
            "name": "Initrode IMO",
            "fein": "12-3456789",
        },
        "carriers": [
            {
                "carrierId": "allianz",
                "carrierName": "Allianz",
                "licensed": True,
                "requirements": {
                    "requiresLetterOfInstruction": True,
                    "requiresTermsOfInstruction": True,
                    "minimumDaysInCurrentHierarchy": 180,
                },
            },
            {
                "carrierId": "american-equity",
                "carrierName": "American Equity",
                "licensed": True,
                "requirements": {
                    "requiresLetterOfInstruction": False,
                    "requiresTermsOfInstruction": True,
                    "minimumDaysInCurrentHierarchy": 90,
                },
            },
        ],
        "bookOfBusiness": [
            {
                "bookId": "bob_1001_A",
                "carrierId": "allianz",
                "policyCount": 42,
                "annualizedPremium": 1850000.00,
            },
            {
                "bookId": "bob_1001_B",
                "carrierId": "american-equity",
                "policyCount": 17,
                "annualizedPremium": 540000.00,
            },
        ],
    },
    {
        "npn": "222",
        "firstName": "Peter",
        "lastName": "Gibbons",
        "currentImo": {
            "name": "Advisors Excel",
            "fein": "98-7654321",
        },
        "carriers": [
            {
                "carrierId": "allianz",
                "carrierName": "Allianz",
                "licensed": True,
                "requirements": {
                    "requiresLetterOfInstruction": True,
                    "requiresTermsOfInstruction": False,
                    "minimumDaysInCurrentHierarchy": 120,
                },
            },
            {
                "carrierId": "american-equity",
                "carrierName": "American Equity",
                "licensed": True,
                "requirements": {
                    "requiresLetterOfInstruction": False,
                    "requiresTermsOfInstruction": True,
                    "minimumDaysInCurrentHierarchy": 60,
                },
            },
        ],
        "bookOfBusiness": [
            {
                "bookId": "bob_1002_A",
                "carrierId": "allianz",
                "policyCount": 23,
                "annualizedPremium": 950000.00,
            },
            {
                "bookId": "bob_1002_B",
                "carrierId": "american-equity",
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


def get_agent_by_npn(npn: str):
    for agent in AGENTS:
        if agent["npn"] == npn:
            return deepcopy(agent)
    return None
