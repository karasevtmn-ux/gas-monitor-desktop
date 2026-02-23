from dataclasses import dataclass
from typing import Optional

@dataclass
class Link:
    id: int
    url: str
    plaintiff: str
    defendant: str
    court: str
    case_number: str
    comment: str
    region: str
    tz_override: Optional[str]
    status: str
    last_ok_at: Optional[str]
    last_check_at: Optional[str]
    consecutive_failures: int
