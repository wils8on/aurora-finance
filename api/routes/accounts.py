"""Endpoints de contas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_session
from api.schemas import AccountCreate, AccountResponse
from models import User
from services import AccountService, ReferenceQueryService

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _response(item) -> AccountResponse:
    return AccountResponse(
        id=item.id,
        name=item.name,
        institution=item.institution,
        account_type=item.account_type,
        initial_balance=format(item.initial_balance, ".2f"),
        initial_balance_date=item.initial_balance_date,
        is_active=item.is_active,
    )


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AccountResponse]:
    items = ReferenceQueryService(session).list_accounts(current_user.id)
    return [_response(item) for item in items]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountResponse:
    account = AccountService(session).create_account(
        user_id=current_user.id,
        name=payload.name,
        institution=payload.institution,
        account_type=payload.account_type,
        initial_balance=payload.initial_balance,
        initial_balance_date=payload.initial_balance_date,
    )
    return _response(account)
