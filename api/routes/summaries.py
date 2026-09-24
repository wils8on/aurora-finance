"""Endpoint de resumos financeiros."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_session
from api.routes.transactions import get_transaction_query_params, to_filters
from api.schemas.summaries import TransactionSummaryResponse
from api.schemas.transactions import TransactionQueryParams, money_string
from models import User
from services import TransactionQueryService

router = APIRouter(prefix="/transaction-summaries", tags=["transaction-summaries"])


@router.get("", response_model=TransactionSummaryResponse)
def transaction_summary(
    params: Annotated[TransactionQueryParams, Depends(get_transaction_query_params)],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionSummaryResponse:
    summary = TransactionQueryService(session).summarize(
        to_filters(params, current_user.id)
    )
    return TransactionSummaryResponse(
        perspective=params.perspective,
        primary_1=money_string(summary.primary_1),
        primary_2=money_string(summary.primary_2),
        primary_3=money_string(summary.primary_3),
        receivable=money_string(summary.receivable),
        payable=money_string(summary.payable),
    )
