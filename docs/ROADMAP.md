# Aurora Finance — Roadmap

## v0.1 — Foundation

Objetivo:
estabelecer fundação técnica e domínio financeiro básico.

Implementar:

- configuração Python;
- dependências;
- SQLAlchemy;
- Alembic;
- SQLite;
- User;
- Account;
- Category;
- Subcategory;
- Transaction;
- repositories básicos;
- services básicos;
- testes;
- configuração inicial do Streamlit.

Critério de conclusão:

O sistema consegue criar e consultar contas, categorias e movimentações
com persistência e testes automatizados.

---

## v0.2 — Financial Core

Implementar:

- receitas;
- despesas;
- transferências;
- recorrências;
- parcelamentos;
- filtros;
- edição;
- cancelamento;
- estorno;
- visão mensal.

Critério:

Fluxo financeiro cotidiano pode ser administrado pelo Aurora.

---

## v0.3 — Budget

Implementar:

- orçamento mensal;
- orçamento anual;
- itens por categoria;
- orçado x comprometido x realizado;
- Mapa Anual;
- comparativos.

Critério:

Aurora consegue reproduzir conceitualmente e superar a visão da
planilha original.

---

## v0.4 — Commitments

Implementar:

- cartões;
- compras;
- parcelamentos de cartão;
- faturas;
- dívidas;
- parcelas de dívida;
- compromissos futuros.

Critério:

O sistema conhece as obrigações financeiras futuras já contratadas.

---

## v0.5 — Dashboard

Implementar:

- cockpit financeiro;
- receitas;
- despesas;
- resultado;
- saldo;
- orçamento;
- próximos compromissos;
- gráficos;
- indicadores.

Critério:

A situação financeira atual pode ser compreendida rapidamente
pela página inicial.

---

## v0.6 — Planning

Implementar:

- metas;
- projeções;
- runway financeiro;
- cenários;
- eventos hipotéticos;
- comparação de cenários.

Critério:

O usuário consegue avaliar impactos financeiros futuros sem modificar
dados reais.

---

## v0.7 — Aurora Insights

Implementar motor determinístico de insights.

Primeiros indicadores:

- comprometimento;
- concentração de despesas;
- evolução mensal;
- variações;
- compromissos 30/60/90 dias;
- runway;
- tendência de saldo;
- evolução patrimonial.

Critério:

O sistema identifica automaticamente informações relevantes a partir
dos dados.

---

## v0.8 — Import

Implementar:

- importação Excel;
- importação CSV;
- mapeamento de categorias;
- validação;
- preview;
- detecção de possíveis duplicidades;
- importação da planilha original.

Nenhuma importação deve gravar dados antes da confirmação do usuário.

---

## v0.9 — Patrimônio e Investimentos

Implementar:

- contas de investimento;
- ativos;
- movimentações;
- posição;
- patrimônio;
- evolução patrimonial.

---

## v1.0 — Aurora Finance

Critérios:

- fluxo financeiro estável;
- orçamento;
- cartões;
- dívidas;
- patrimônio;
- planejamento;
- insights;
- importação;
- testes das regras críticas;
- migrations consistentes;
- documentação atualizada;
- experiência de uso coerente.
