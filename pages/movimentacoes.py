"""Interface operacional de receitas, despesas e liquidações."""

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
import logging

import streamlit as st

from components.finance import STATUS_LABELS, TYPE_LABELS, due_condition
from database.connection import get_session
from models import CategoryType, DerivedTransactionStatus, TransactionType
from services import (
    DatePerspective,
    ReferenceQueryService,
    TransactionFilters,
    TransactionQueryService,
    TransactionService,
    TransactionServiceError,
)
from utils.app_context import get_operational_user_id
from utils.formatting import format_currency, format_date, format_datetime, localize_datetime, parse_decimal

PERSPECTIVE_LABELS = {
    DatePerspective.COMPETENCE: "Competência",
    DatePerspective.DUE: "Vencimento",
    DatePerspective.CASH: "Caixa",
}
PERSPECTIVE_HELP = {
    DatePerspective.COMPETENCE: "Período aplicado à competência econômica.",
    DatePerspective.DUE: "Período aplicado ao vencimento das obrigações.",
    DatePerspective.CASH: "Período aplicado à data das liquidações.",
}
STATE_OPTIONS = {
    None: "Todos (sem canceladas)",
    DerivedTransactionStatus.PENDING: "Pendente",
    DerivedTransactionStatus.PARTIAL: "Parcial",
    DerivedTransactionStatus.SETTLED: "Liquidada",
    DerivedTransactionStatus.CANCELLED: "Cancelada",
}
LOGGER = logging.getLogger(__name__)


def current_month() -> tuple[date, date]:
    today = date.today()
    return today.replace(day=1), today.replace(day=monthrange(today.year, today.month)[1])


def initialize_state() -> None:
    start, end = current_month()
    defaults = {
        "transaction_perspective": DatePerspective.COMPETENCE,
        "transaction_start": start,
        "transaction_end": end,
        "transaction_page": 1,
        "transaction_form_open": False,
        "selected_transaction_id": None,
        "settlement_transaction_id": None,
        "cancel_transaction_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def main() -> None:
    user_id = get_operational_user_id()
    initialize_state()
    title, action = st.columns([4, 1])
    with title:
        st.title("Movimentações")
        st.caption("Receitas e despesas por competência, vencimento ou caixa.")
    with action:
        if st.button("Nova movimentação", type="primary", use_container_width=True):
            st.session_state.transaction_form_open = True

    if st.session_state.transaction_form_open:
        new_transaction_dialog(user_id)
    if st.session_state.get("settlement_transaction_id"):
        settlement_dialog(user_id, st.session_state.settlement_transaction_id)
    if st.session_state.get("cancel_transaction_id"):
        cancellation_dialog(user_id, st.session_state.cancel_transaction_id)

    filters = render_filters(user_id)
    with get_session() as session:
        query_service = TransactionQueryService(session)
        summary = query_service.summarize(filters)
        result = query_service.list_transactions(filters)
    render_summary(filters.perspective, summary)
    render_listing(result, filters.perspective)
    render_pagination(result.pages)

    selected_id = st.session_state.get("selected_transaction_id")
    if selected_id:
        with get_session() as session:
            detail = TransactionQueryService(session).get_detail(selected_id, user_id)
        if detail:
            render_detail(detail)
        else:
            st.session_state.selected_transaction_id = None


def render_filters(user_id: int) -> TransactionFilters:
    perspective = st.segmented_control(
        "Perspectiva temporal",
        options=list(PERSPECTIVE_LABELS),
        format_func=lambda item: PERSPECTIVE_LABELS[item],
        key="transaction_perspective",
    ) or DatePerspective.COMPETENCE
    st.caption(PERSPECTIVE_HELP[perspective])
    period_col, type_col, state_col = st.columns([2, 1, 1])
    with period_col:
        period = st.date_input(
            "Período",
            value=(st.session_state.transaction_start, st.session_state.transaction_end),
            format="DD/MM/YYYY",
        )
        start_date, end_date = period if isinstance(period, tuple) and len(period) == 2 else (period, period)
        st.session_state.transaction_start = start_date
        st.session_state.transaction_end = end_date
    with type_col:
        type_filter = st.selectbox(
            "Tipo",
            [None, TransactionType.INCOME, TransactionType.EXPENSE],
            format_func=lambda item: "Todos" if item is None else TYPE_LABELS[item],
        )
    with state_col:
        state_filter = st.selectbox(
            "Estado", list(STATE_OPTIONS), format_func=lambda item: STATE_OPTIONS[item]
        )

    with get_session() as session:
        categories = ReferenceQueryService(session).list_categories(user_id)
    category_col, subcategory_col, search_col = st.columns([1, 1, 2])
    with category_col:
        category = st.selectbox(
            "Categoria",
            [None, *categories],
            format_func=lambda item: "Todas" if item is None else item.name,
        )
    with subcategory_col:
        subcategory = st.selectbox(
            "Subcategoria",
            [None, *(category.subcategories if category else ())],
            format_func=lambda item: "Todas" if item is None else item.name,
            disabled=category is None,
        )
    with search_col:
        search = st.text_input("Buscar", placeholder="Descrição, categoria ou subcategoria")
    signature = (
        perspective,
        start_date,
        end_date,
        type_filter,
        state_filter,
        category.id if category else None,
        subcategory.id if subcategory else None,
        search,
    )
    if st.session_state.get("transaction_filter_signature") not in (None, signature):
        st.session_state.transaction_page = 1
        st.session_state.selected_transaction_id = None
    st.session_state.transaction_filter_signature = signature
    return TransactionFilters(
        user_id=user_id,
        perspective=perspective,
        start_date=start_date,
        end_date=end_date,
        transaction_type=type_filter,
        derived_status=state_filter,
        category_id=category.id if category else None,
        subcategory_id=subcategory.id if subcategory else None,
        search=search,
        include_cancelled=state_filter == DerivedTransactionStatus.CANCELLED,
        page=st.session_state.transaction_page,
    )


def render_summary(perspective, summary) -> None:
    labels = {
        DatePerspective.COMPETENCE: ("Receitas", "Despesas", "Resultado"),
        DatePerspective.DUE: ("A receber", "A pagar", "Vencido"),
        DatePerspective.CASH: ("Recebido", "Pago", "Fluxo líquido"),
    }[perspective]
    values = (summary.primary_1, summary.primary_2, summary.primary_3)
    for column, label, value in zip(st.columns(3), labels, values):
        column.metric(label, format_currency(value))
    if perspective == DatePerspective.COMPETENCE:
        st.caption(
            f"A receber: {format_currency(summary.receivable)}  •  "
            f"A pagar: {format_currency(summary.payable)}"
        )


def render_listing(result, perspective: DatePerspective) -> None:
    st.subheader("Movimentações")
    if not result.items:
        st.info("Nenhuma movimentação corresponde ao período e aos filtros selecionados.")
        return
    rows = []
    for item in result.items:
        category = item.category_name + (f" › {item.subcategory_name}" if item.subcategory_name else "")
        values = f"{format_currency(item.settled_amount)} de {format_currency(item.amount)}"
        if item.remaining_amount > Decimal("0.00"):
            values += f" · restam {format_currency(item.remaining_amount)}"
        if perspective == DatePerspective.CASH:
            values += f" · no período {format_currency(item.period_settled_amount)}"
        condition = due_condition(item.due_date, item.derived_status, item.remaining_amount)
        rows.append(
            {
                "Descrição": item.description,
                "Categoria": category,
                "Referência": format_date(item.reference_date),
                "Valores": values,
                "Estado": STATUS_LABELS[item.derived_status] + (f" · {condition}" if condition else ""),
            }
        )
    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="transaction_table",
    )
    if event.selection.rows:
        st.session_state.selected_transaction_id = result.items[event.selection.rows[0]].id
    st.caption(f"{result.total} resultado(s) · página {result.page} de {result.pages}")


def render_pagination(pages: int) -> None:
    previous, current, following = st.columns([1, 2, 1])
    if previous.button("← Anterior", disabled=st.session_state.transaction_page <= 1, use_container_width=True):
        st.session_state.transaction_page -= 1
        st.rerun()
    current.markdown(f"<p style='text-align:center'>Página {st.session_state.transaction_page} de {pages}</p>", unsafe_allow_html=True)
    if following.button("Próxima →", disabled=st.session_state.transaction_page >= pages, use_container_width=True):
        st.session_state.transaction_page += 1
        st.rerun()


def render_detail(detail) -> None:
    st.divider()
    st.subheader(detail.description)
    condition = due_condition(detail.due_date, detail.derived_status, detail.remaining_amount)
    st.write(
        f"**{TYPE_LABELS[detail.transaction_type]}** · {STATUS_LABELS[detail.derived_status]}"
        + (f" · {condition}" if condition else "")
    )
    nominal, settled, remaining = st.columns(3)
    nominal.metric("Valor nominal", format_currency(detail.amount))
    settled.metric("Liquidado", format_currency(detail.settled_amount))
    remaining.metric("Restante", format_currency(detail.remaining_amount))
    category = detail.category_name + (f" › {detail.subcategory_name}" if detail.subcategory_name else "")
    st.write(f"**Categoria:** {category}")
    st.write(f"**Competência:** {format_date(detail.competence_date)}")
    st.write(f"**Vencimento:** {format_date(detail.due_date)}")
    if detail.notes:
        st.write(f"**Observações:** {detail.notes}")
    if detail.cancellation_reason:
        st.write(f"**Motivo do cancelamento:** {detail.cancellation_reason}")
    st.markdown("#### Histórico de liquidações")
    if detail.settlements:
        st.dataframe(
            [
                {
                    "Conta": item.account_name,
                    "Data e hora": format_datetime(item.settled_at),
                    "Valor": format_currency(item.amount),
                    "Observação": item.notes or "—",
                }
                for item in detail.settlements
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Nenhuma liquidação registrada.")
    action, cancellation = st.columns(2)
    if detail.derived_status in (DerivedTransactionStatus.PENDING, DerivedTransactionStatus.PARTIAL):
        if action.button("Registrar liquidação", type="primary", use_container_width=True):
            st.session_state.settlement_transaction_id = detail.id
            st.rerun()
    if detail.derived_status == DerivedTransactionStatus.PENDING:
        if cancellation.button("Cancelar movimentação", use_container_width=True):
            st.session_state.cancel_transaction_id = detail.id
            st.rerun()
    elif detail.derived_status in (
        DerivedTransactionStatus.PARTIAL,
        DerivedTransactionStatus.SETTLED,
    ):
        cancellation.info("Já houve movimentação financeira; cancelamento simples indisponível.")


@st.dialog("Nova movimentação", width="large")
def new_transaction_dialog(user_id: int) -> None:
    transaction_type = st.segmented_control(
        "Tipo *",
        options=[TransactionType.INCOME, TransactionType.EXPENSE],
        format_func=lambda item: TYPE_LABELS[item],
        default=TransactionType.EXPENSE,
        key="new_transaction_type",
    )
    with get_session() as session:
        reference = ReferenceQueryService(session)
        categories = reference.list_categories(user_id, category_type=CategoryType(transaction_type.value), active_only=True)
        accounts = reference.list_accounts(user_id, active_only=True)
    if not categories:
        st.warning("Cadastre uma categoria compatível antes de continuar.")
        if st.button("Ir para Categorias"):
            st.session_state.transaction_form_open = False
            st.switch_page("pages/categorias.py")
        return
    description = st.text_input("Descrição *")
    amount_text = st.text_input("Valor nominal *", placeholder="0,00")
    category = st.selectbox("Categoria *", categories, format_func=lambda item: item.name)
    subcategory = st.selectbox(
        "Subcategoria",
        [None, *category.subcategories],
        format_func=lambda item: "Sem subcategoria" if item is None else item.name,
    )
    competence_date = st.date_input("Competência *", value=date.today(), format="DD/MM/YYYY")
    has_due_date = st.checkbox("Possui vencimento?", value=False)
    due_date = st.date_input("Vencimento", value=date.today(), format="DD/MM/YYYY", disabled=not has_due_date)
    notes = st.text_area("Observações")
    settled_label = "Já foi recebida?" if transaction_type == TransactionType.INCOME else "Já foi paga?"
    already_settled = st.checkbox(settled_label, value=False)
    account = settled_date = settled_time = settlement_notes = None
    if already_settled:
        if not accounts:
            st.warning("Cadastre uma conta antes de registrar uma liquidação.")
            if st.button("Ir para Contas"):
                st.session_state.transaction_form_open = False
                st.switch_page("pages/contas.py")
            return
        account = st.selectbox("Conta *", accounts, format_func=lambda item: item.name)
        st.text_input("Valor da liquidação", value=amount_text or "Igual ao valor nominal", disabled=True)
        settled_date = st.date_input("Data da liquidação *", value=date.today(), format="DD/MM/YYYY")
        settled_time = st.time_input("Horário *", value=datetime.now().time().replace(microsecond=0))
        settlement_notes = st.text_area("Observação da liquidação")
    if st.button("Cadastrar movimentação", type="primary", use_container_width=True):
        try:
            amount = parse_decimal(amount_text)
            with get_session() as session:
                service = TransactionService(session)
                if already_settled:
                    service.create_settled_historical_transaction(
                        user_id=user_id,
                        category_id=category.id,
                        subcategory_id=subcategory.id if subcategory else None,
                        account_id=account.id,
                        transaction_type=transaction_type,
                        description=description,
                        amount=amount,
                        competence_date=competence_date,
                        due_date=due_date if has_due_date else None,
                        settled_at=localize_datetime(settled_date, settled_time),
                        transaction_notes=notes or None,
                        settlement_notes=settlement_notes or None,
                    )
                else:
                    service.create_transaction(
                        user_id=user_id,
                        category_id=category.id,
                        subcategory_id=subcategory.id if subcategory else None,
                        transaction_type=transaction_type,
                        description=description,
                        amount=amount,
                        competence_date=competence_date,
                        due_date=due_date if has_due_date else None,
                        notes=notes or None,
                    )
        except (ValueError, TransactionServiceError) as error:
            st.error(humanize_error(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao cadastrar movimentação")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.transaction_form_open = False
            st.toast("Movimentação cadastrada com sucesso.", icon="✓")
            st.rerun()


@st.dialog("Registrar liquidação")
def settlement_dialog(user_id: int, transaction_id: int) -> None:
    with get_session() as session:
        detail = TransactionQueryService(session).get_detail(transaction_id, user_id)
        accounts = ReferenceQueryService(session).list_accounts(user_id, active_only=True)
    if detail is None:
        st.error("Movimentação não encontrada.")
        return
    if not accounts:
        st.warning("Cadastre uma conta antes de registrar uma liquidação.")
        if st.button("Ir para Contas"):
            st.session_state.settlement_transaction_id = None
            st.switch_page("pages/contas.py")
        return
    st.caption(f"Restante: {format_currency(detail.remaining_amount)}")
    account = st.selectbox("Conta *", accounts, format_func=lambda item: item.name)
    amount_text = st.text_input("Valor *", value=str(detail.remaining_amount).replace(".", ","))
    settled_date = st.date_input("Data *", value=date.today(), format="DD/MM/YYYY")
    settled_time = st.time_input("Horário *", value=datetime.now().time().replace(microsecond=0))
    notes = st.text_area("Observação")
    if st.button("Confirmar liquidação", type="primary", use_container_width=True):
        try:
            amount = parse_decimal(amount_text)
            if amount > detail.remaining_amount:
                raise ValueError(f"O valor informado supera o restante de {format_currency(detail.remaining_amount)}.")
            with get_session() as session:
                TransactionService(session).add_settlement(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    account_id=account.id,
                    amount=amount,
                    settled_at=localize_datetime(settled_date, settled_time),
                    notes=notes or None,
                )
        except (ValueError, TransactionServiceError) as error:
            st.error(humanize_error(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao registrar liquidação")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.settlement_transaction_id = None
            st.toast("Liquidação registrada com sucesso.", icon="✓")
            st.rerun()


@st.dialog("Cancelar movimentação")
def cancellation_dialog(user_id: int, transaction_id: int) -> None:
    st.warning("O cancelamento preserva o registro e não pode ser desfeito nesta versão.")
    reason = st.text_area("Motivo (opcional)")
    confirmed = st.checkbox("Confirmo o cancelamento desta movimentação.")
    if st.button("Confirmar cancelamento", type="primary", disabled=not confirmed):
        try:
            with get_session() as session:
                TransactionService(session).cancel_transaction(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    cancellation_reason=reason or None,
                )
        except TransactionServiceError as error:
            st.error(humanize_error(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao cancelar movimentação")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.cancel_transaction_id = None
            st.toast("Movimentação cancelada.", icon="✓")
            st.rerun()


def humanize_error(error: Exception) -> str:
    replacements = {
        "Description é obrigatória.": "Informe uma descrição.",
        "Category incompatível com TransactionType.": "A categoria não corresponde ao tipo escolhido.",
        "Subcategory não pertence à Category informada.": "A subcategoria não pertence à categoria selecionada.",
        "Settlements não podem exceder o valor nominal.": "O valor supera o restante da movimentação.",
        "Transaction com Settlement não pode ser cancelada.": "Não é possível cancelar porque já houve movimentação financeira.",
    }
    return replacements.get(str(error), str(error))


main()
