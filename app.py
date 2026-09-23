"""Ponto de entrada da primeira vertical slice do Aurora Finance."""

import streamlit as st

st.set_page_config(page_title="Aurora Finance", page_icon="🌅", layout="wide")

navigation = st.navigation(
    [
        st.Page("pages/movimentacoes.py", title="Movimentações", icon="🧾", default=True),
        st.Page("pages/contas.py", title="Contas", icon="🏦"),
        st.Page("pages/categorias.py", title="Categorias", icon="🏷️"),
    ]
)
navigation.run()
