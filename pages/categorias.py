"""Cadastro e consulta da hierarquia de categorias."""

import logging

import streamlit as st

from database.connection import get_session
from models import CategoryType
from services import CategoryService, ReferenceQueryService, ReferenceServiceError
from utils.app_context import get_operational_user_id

TYPE_LABELS = {CategoryType.INCOME: "Receita", CategoryType.EXPENSE: "Despesa"}
LOGGER = logging.getLogger(__name__)


def main() -> None:
    user_id = get_operational_user_id()
    title, action = st.columns([4, 1])
    with title:
        st.title("Categorias")
        st.caption("Classifique a natureza econômica das receitas e despesas.")
    with action:
        if st.button("Nova categoria", type="primary", use_container_width=True):
            st.session_state.category_form_open = True

    if st.session_state.get("category_form_open"):
        category_dialog(user_id)
    if st.session_state.get("subcategory_category_id"):
        subcategory_dialog(user_id, st.session_state.subcategory_category_id)

    with get_session() as session:
        categories = ReferenceQueryService(session).list_categories(user_id)

    if not categories:
        st.info("Nenhuma categoria cadastrada. Crie categorias para registrar movimentações.")
        return

    income_tab, expense_tab = st.tabs(["Receitas", "Despesas"])
    render_category_group(income_tab, categories, CategoryType.INCOME)
    render_category_group(expense_tab, categories, CategoryType.EXPENSE)


def render_category_group(container, categories, category_type: CategoryType) -> None:
    matching = [item for item in categories if item.category_type == category_type]
    with container:
        if not matching:
            st.info(f"Nenhuma categoria de {TYPE_LABELS[category_type].lower()} cadastrada.")
            return
        for category in matching:
            with st.container(border=True):
                heading, action = st.columns([4, 1])
                heading.markdown(
                    f"**{category.name}**  \n{'Ativa' if category.is_active else 'Inativa'}"
                )
                if action.button(
                    "Adicionar subcategoria",
                    key=f"subcategory_{category.id}",
                    disabled=not category.is_active,
                    use_container_width=True,
                ):
                    st.session_state.subcategory_category_id = category.id
                    st.rerun()
                active = [item for item in category.subcategories if item.is_active]
                inactive = [item for item in category.subcategories if not item.is_active]
                if active:
                    st.write(" • ".join(item.name for item in active))
                else:
                    st.caption("Sem subcategorias.")
                if inactive:
                    st.caption("Inativas: " + ", ".join(item.name for item in inactive))


@st.dialog("Nova categoria")
def category_dialog(user_id: int) -> None:
    with st.form("new_category_form"):
        category_type = st.segmented_control(
            "Natureza *",
            options=list(TYPE_LABELS),
            format_func=lambda item: TYPE_LABELS[item],
            default=CategoryType.EXPENSE,
        )
        name = st.text_input("Nome *")
        submitted = st.form_submit_button("Cadastrar categoria", type="primary")
    if submitted:
        try:
            with get_session() as session:
                CategoryService(session).create_category(
                    user_id=user_id, name=name, category_type=category_type
                )
        except ReferenceServiceError as error:
            st.error(str(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao cadastrar categoria")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.category_form_open = False
            st.toast("Categoria cadastrada com sucesso.", icon="✓")
            st.rerun()


@st.dialog("Nova subcategoria")
def subcategory_dialog(user_id: int, category_id: int) -> None:
    with st.form("new_subcategory_form"):
        name = st.text_input("Nome *")
        submitted = st.form_submit_button("Cadastrar subcategoria", type="primary")
    if submitted:
        try:
            with get_session() as session:
                CategoryService(session).create_subcategory(
                    user_id=user_id, category_id=category_id, name=name
                )
        except ReferenceServiceError as error:
            st.error(str(error))
        except Exception:
            LOGGER.exception("Falha inesperada ao cadastrar subcategoria")
            st.error("Não foi possível concluir a operação. Tente novamente.")
        else:
            st.session_state.subcategory_category_id = None
            st.toast("Subcategoria cadastrada com sucesso.", icon="✓")
            st.rerun()


main()
