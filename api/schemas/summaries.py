"""Schema HTTP dos resumos financeiros."""

from pydantic import BaseModel

from services import DatePerspective


class TransactionSummaryResponse(BaseModel):
    perspective: DatePerspective
    primary_1: str
    primary_2: str
    primary_3: str
    receivable: str
    payable: str
