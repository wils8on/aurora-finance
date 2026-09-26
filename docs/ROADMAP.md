# Aurora Finance — Roadmap

## v0.1 — Foundation — concluída

Entregue:

- configuração Python;
- SQLAlchemy, Alembic e SQLite;
- User, Account, Category e Subcategory;
- Transaction e Settlement;
- repositories e services básicos;
- query services para competência, vencimento e caixa;
- constraints, ownership, estados derivados e atomicidade;
- testes automatizados;
- primeira vertical slice funcional em Streamlit para Movimentações, Contas e
  Categorias.

O Streamlit passa a ser baseline temporário de equivalência, não a interface
definitiva.

Critério atingido: o sistema cria e consulta contas, categorias, Transactions e
Settlements com persistência e testes, mantendo separadas as dimensões econômica
e de caixa.

---

## Marco atual — Web Platform Migration

Objetivo: migrar a apresentação para React/TypeScript/Vite + FastAPI sem alterar
ou duplicar as regras financeiras existentes.

Ordem aprovada:

1. atualizar a documentação — concluído;
2. preparar a application layer e estabilizar query services/DTOs — concluído;
3. adicionar FastAPI como adaptador HTTP — fluxos da vertical slice concluídos;
4. criar testes de integração da API — cobertura financeira concluída;
5. criar a fundação React/Vite — concluído;
6. reproduzir Contas e Categorias — concluído;
7. reproduzir Movimentações — concluído;
8. validar equivalência funcional e financeira — concluído;
9. implementar autenticação, sessão, CSRF e proteção das APIs — concluído;
10. validar backend e suíte financeira em PostgreSQL real — concluído;
11. preparar frontend, backend e banco de produção — próximo passo;
12. remover Streamlit.

A API atualmente expõe health, contas, categorias, subcategorias, Transaction,
Settlement, cancelamento e resumos por competência, vencimento e caixa.
Autenticação real está implementada com Argon2id, sessão opaca revogável,
cookie HttpOnly, proteção CSRF e ownership derivado da sessão. Todas as
migrations, autenticação, ownership e o oráculo financeiro foram validados em
PostgreSQL 17.11 real, inclusive `timestamptz` no limite operacional de
`America/Sao_Paulo` e múltiplos Settlements. O deploy e a validação operacional
no provedor de produção permanecem pendentes.

A auditoria de paridade validou os mesmos resultados financeiros na vertical
slice Streamlit e em React + FastAPI. A perspectiva Caixa utiliza o dia
operacional `America/Sao_Paulo` para filtragem, referência, ordenação e resumos.
O Streamlit permanece temporariamente no repositório, elegível para
aposentadoria, mas aguardando decisão explícita e o cumprimento dos demais
critérios de retirada abaixo.

A foundation web implementa React/TypeScript/Vite, `HashRouter`, Aurora UI v1,
shell responsivo, navegação lateral, componentes reutilizáveis e cliente HTTP
estruturado. Contas, Categorias e Subcategorias possuem listagem e cadastro
integrados à API, com estados de carregamento, vazio, erro e sucesso.
Movimentações oferece perspectivas de competência, vencimento e caixa, período
mensal, filtros e paginação server-side, summaries reais, criação pendente ou
historicamente liquidada, detalhe, histórico de liquidações, Settlement parcial
e integral e cancelamento quando permitido. O deploy no GitHub Pages ainda não
foi realizado.

Durante este marco ficam bloqueados:

- Transfer;
- Recurrence;
- Installment;
- CreditCard;
- Debt;
- Budget;
- Goal;
- Scenario;
- Investment;
- Aurora Insights.

### Critério de equivalência

React + FastAPI devem reproduzir:

- listagem e cadastro de contas;
- listagem e cadastro de categorias e subcategorias;
- criação de movimentação pendente;
- criação já integralmente liquidada;
- listagem, filtros, paginação e detalhe;
- Settlement parcial e integral;
- cancelamento permitido;
- bloqueio do cancelamento quando houver Settlement;
- perspectivas de competência, vencimento e caixa;
- estados vazios, tratamento de erros e formatação pt-BR;
- os mesmos resultados financeiros da vertical slice Streamlit.

### Critério de retirada do Streamlit

Além da equivalência, são obrigatórios:

- autenticação adequada em produção;
- frontend publicado;
- backend seguro em HTTPS;
- testes críticos aprovados;
- documentação atualizada.

---

## v0.2 — Financial Core

Somente após Web Platform Migration:

- Transfer;
- recorrências;
- parcelamentos;
- edição controlada;
- estorno;
- operações financeiras completas;
- visão mensal ampliada.

Critério: o fluxo financeiro cotidiano pode ser administrado pela interface web
definitiva.

---

## v0.3 — Budget

- orçamento mensal e anual;
- itens por categoria;
- orçado x comprometido x realizado;
- Mapa Anual;
- comparativos.

Critério: Aurora reproduz conceitualmente e supera a visão da planilha original.

---

## v0.4 — Commitments

- cartões e compras;
- parcelamentos de cartão;
- faturas;
- dívidas e parcelas;
- compromissos futuros.

Critério: Aurora conhece obrigações financeiras futuras já contratadas.

---

## v0.5 — Dashboard

- cockpit financeiro;
- receitas, despesas e resultado;
- saldo;
- orçamento;
- próximos compromissos;
- gráficos e indicadores com finalidade explícita.

Critério: a situação financeira atual pode ser compreendida rapidamente.

---

## v0.6 — Planning

- metas;
- projeções;
- runway financeiro;
- cenários e eventos hipotéticos;
- comparação de cenários.

Critério: decisões futuras podem ser avaliadas sem modificar dados reais.

---

## v0.7 — Aurora Insights

Motor determinístico para:

- comprometimento;
- concentração de despesas;
- evolução mensal;
- variações;
- compromissos 30/60/90 dias;
- runway;
- tendência de saldo;
- evolução patrimonial.

---

## v0.8 — Import

- Excel e CSV;
- mapeamento de categorias;
- validação e preview;
- detecção de possíveis duplicidades;
- importação da planilha original.

Nenhuma importação grava dados antes de confirmação.

---

## v0.9 — Patrimônio e Investimentos

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
- cartões e dívidas;
- patrimônio;
- planejamento e insights;
- importação;
- testes das regras críticas;
- migrations consistentes;
- documentação atualizada;
- experiência web coerente.
