"""Cadastro e consulta de contas."""

from datetime import date
import logging

import streamlit as st

from database.connection import get_session
from models import AccountType
from services import AccountService, ReferenceQueryService, ReferenceServiceError
from utils.app_context import get_operational_user_id
from utils.formatting import format_currency, format_date, parse_decimal

ACCOUNT_TYPE_LABELS = {
    AccountType.CHECKING: "Conta corrente",
    AccountType.SAVINGS: "Poupança",
    AccountType.CASH: "Dinheiro",
    AccountType.DIGITAL: "Conta digital",
    AccountType.OTHER: "Outra",
}
LOGGER = logging.getLogger(__name__)


def main() -> None:
    user_id = get_operational_user_id()
    title, action = st.columns([4, 1])
    with title:
        st.title("Contas")
        st.caption("Locais onde seus recursos financeiros estão mantidos.")
    with action:
        if st.button("Nova conta", type="primary", use_container_width=True):
            st.session_state.account_form_open = True

    if st.session_state.get("account_form_open"):
        account_dialog(user_id)

    with get_session() as session:
        accounts = ReferenceQueryService(session).list_accounts(user_id)

    if not accounts:
        st.info("Nenhuma conta cadastrada. Cadastre uma conta para registrar liquidações.")
        return

    rows = [
        {
            "Nome": item.name,
            "Instituição": item.institution or "—",
            "Tipo": ACCOUNT_TYPE_LABELS[AccountType(item.account_type)],
            "Saldo inicial": format_currency(item.initial_balance),
            "Data-base": format_date(item.initial_balance_date),
            "Situação": "Ativa" if item.is_active else "Inativa",
        }
        for item in accounts
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("O saldo atual não é armazenado: ele será calculado a partir dos eventos financeiros.")


@st.dialog("Nova conta")
def account_dialog(user_id: int) -> None:
    with st.form("new_account_form"):
        name = st.text_input("Nome da conta *")
        institution = st.text_input("Instituição")
        account_type = st.selectbox(
            "Tipo *",
            list(ACCOUNT_TYPE_LABELS),
            format_func=lambda item: ACCOUNT_TYPE_LABELS[item],
        )
        initial_balance_text = st.text_input("Saldo inicial *", value="0,00")
        has_balance_date = st.checkbox("Informar data-base do saldo inicial", value=True)
        balance_date = st.date_input("Data-base", value=date.today(), disabled=not has_balance_date)
        submitted = st.form_submit_button("Cadastrar conta", type="primary")

    if submitted:
        try:
            initial_balance = parse_decimal(initial_balance_text)
            with get_session() as session:
                AccountService(session).create_account(
                    user_id=user_id,
                    name=name,
                    institution=institution,
                    account_type=account_type,
                    initial_balance=initial_balance,
                    initial_balance_date=balance_date if has_balance_date else None,
                )
        except (ValueError, ReferenceServiceError) as error:
            st.error(str(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao cadastrar conta")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.account_form_open = False
            st.toast("Conta cadastrada com sucesso.", icon="✓")
            st.rerun()


main()
