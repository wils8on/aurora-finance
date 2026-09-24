"""Endpoints de Transactions, Settlements e cancelamento."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_session
from api.schemas.transactions import (
    CancellationCreate,
    CancellationResponse,
    NamedReference,
    PaginationResponse,
    SettlementCreate,
    SettlementResponse,
    SettledTransactionCreate,
    TransactionCreate,
    TransactionDetailResponse,
    TransactionListItemResponse,
    TransactionPageResponse,
    TransactionQueryParams,
    aware_utc,
    money_string,
)
from models import DerivedTransactionStatus, TransactionType, User
from services import (
    DatePerspective,
    NotFoundError,
    TransactionFilters,
    TransactionQueryService,
    TransactionService,
    ValidationError,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_query_params(
    start_date: date,
    end_date: date,
    perspective: DatePerspective = DatePerspective.COMPETENCE,
    transaction_type: TransactionType | None = None,
    derived_status: DerivedTransactionStatus | None = None,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    search: str = "",
    include_cancelled: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> TransactionQueryParams:
    if start_date > end_date:
        raise ValidationError(
            "start_date não pode ser posterior a end_date.",
            code="INVALID_DATE_RANGE",
            field="start_date",
        )
    return TransactionQueryParams(
        perspective=perspective,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        derived_status=derived_status,
        category_id=category_id,
        subcategory_id=subcategory_id,
        search=search,
        include_cancelled=include_cancelled,
        page=page,
        page_size=page_size,
    )


def to_filters(params: TransactionQueryParams, user_id: int) -> TransactionFilters:
    return TransactionFilters(
        user_id=user_id,
        start_date=params.start_date,
        end_date=params.end_date,
        perspective=params.perspective,
        transaction_type=params.transaction_type,
        derived_status=params.derived_status,
        category_id=params.category_id,
        subcategory_id=params.subcategory_id,
        search=params.search,
        include_cancelled=params.include_cancelled,
        page=params.page,
        page_size=params.page_size,
    )


def detail_response(detail) -> TransactionDetailResponse:
    cancellation = None
    if detail.cancelled_at is not None:
        cancellation = CancellationResponse(
            cancelled_at=aware_utc(detail.cancelled_at),
            reason=detail.cancellation_reason,
        )
    return TransactionDetailResponse(
        id=detail.id,
        transaction_type=detail.transaction_type,
        persisted_status=detail.persisted_status,
        derived_status=detail.derived_status,
        description=detail.description,
        amount=money_string(detail.amount),
        settled_amount=money_string(detail.settled_amount),
        remaining_amount=money_string(detail.remaining_amount),
        competence_date=detail.competence_date,
        due_date=detail.due_date,
        category=NamedReference(id=detail.category_id, name=detail.category_name),
        subcategory=(
            NamedReference(id=detail.subcategory_id, name=detail.subcategory_name)
            if detail.subcategory_id is not None and detail.subcategory_name is not None
            else None
        ),
        notes=detail.notes,
        cancellation=cancellation,
        settlements=[
            SettlementResponse(
                id=item.id,
                account=NamedReference(id=item.account_id, name=item.account_name),
                amount=money_string(item.amount),
                settled_at=aware_utc(item.settled_at),
                notes=item.notes,
            )
            for item in detail.settlements
        ],
    )


def get_detail_or_404(
    session: Session, transaction_id: int, user_id: int
) -> TransactionDetailResponse:
    detail = TransactionQueryService(session).get_detail(transaction_id, user_id)
    if detail is None:
        raise NotFoundError(
            "Transaction não encontrada.",
            code="TRANSACTION_NOT_FOUND",
            field="transaction_id",
        )
    return detail_response(detail)


@router.get("", response_model=TransactionPageResponse)
def list_transactions(
    params: Annotated[TransactionQueryParams, Depends(get_transaction_query_params)],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionPageResponse:
    result = TransactionQueryService(session).list_transactions(
        to_filters(params, current_user.id)
    )
    return TransactionPageResponse(
        items=[
            TransactionListItemResponse(
                id=item.id,
                transaction_type=item.transaction_type,
                derived_status=item.derived_status,
                description=item.description,
                amount=money_string(item.amount),
                settled_amount=money_string(item.settled_amount),
                remaining_amount=money_string(item.remaining_amount),
                period_settled_amount=money_string(item.period_settled_amount),
                competence_date=item.competence_date,
                due_date=item.due_date,
                reference_date=item.reference_date,
                category=NamedReference(id=item.category_id, name=item.category_name),
                subcategory=(
                    NamedReference(id=item.subcategory_id, name=item.subcategory_name)
                    if item.subcategory_id is not None and item.subcategory_name is not None
                    else None
                ),
            )
            for item in result.items
        ],
        pagination=PaginationResponse(
            page=result.page,
            page_size=result.page_size,
            total_items=result.total,
            total_pages=result.pages,
        ),
    )


@router.post("", response_model=TransactionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionDetailResponse:
    transaction = TransactionService(session).create_transaction(
        user_id=current_user.id,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        transaction_type=payload.transaction_type,
        description=payload.description,
        amount=payload.amount,
        competence_date=payload.competence_date,
        due_date=payload.due_date,
        notes=payload.notes,
    )
    return get_detail_or_404(session, transaction.id, current_user.id)


@router.post(
    "/settled",
    response_model=TransactionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_settled_transaction(
    payload: SettledTransactionCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionDetailResponse:
    transaction, _settlement = TransactionService(
        session
    ).create_settled_historical_transaction(
        user_id=current_user.id,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        account_id=payload.settlement.account_id,
        transaction_type=payload.transaction_type,
        description=payload.description,
        amount=payload.amount,
        competence_date=payload.competence_date,
        due_date=payload.due_date,
        settled_at=payload.settlement.settled_at,
        transaction_notes=payload.transaction_notes,
        settlement_notes=payload.settlement.notes,
    )
    return get_detail_or_404(session, transaction.id, current_user.id)


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
def get_transaction(
    transaction_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionDetailResponse:
    return get_detail_or_404(session, transaction_id, current_user.id)


@router.post(
    "/{transaction_id}/settlements",
    response_model=TransactionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_settlement(
    transaction_id: int,
    payload: SettlementCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionDetailResponse:
    TransactionService(session).add_settlement(
        transaction_id=transaction_id,
        user_id=current_user.id,
        account_id=payload.account_id,
        amount=payload.amount,
        settled_at=payload.settled_at,
        notes=payload.notes,
    )
    return get_detail_or_404(session, transaction_id, current_user.id)


@router.post(
    "/{transaction_id}/cancellation",
    response_model=TransactionDetailResponse,
)
def cancel_transaction(
    transaction_id: int,
    payload: CancellationCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TransactionDetailResponse:
    TransactionService(session).cancel_transaction(
        transaction_id=transaction_id,
        user_id=current_user.id,
        cancellation_reason=payload.reason,
    )
    return get_detail_or_404(session, transaction_id, current_user.id)
