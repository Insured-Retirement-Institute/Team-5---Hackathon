from enum import Enum


class Status(Enum):
    PENDING = 1
    COMPLETED = 2
    CANCELED = 3
    REJECTED = 4
    INITIATED = 5
    RELEASED = 6


# Status:
# receiving_fein
# releasing_fein
# carrier
# npn
# status
