# Aurora Finance

Aurora Finance é uma plataforma pessoal de gestão, planejamento e inteligência
financeira. O projeto separa compromissos econômicos (`Transaction`) de eventos
de caixa (`Settlement`) e prioriza rastreabilidade e consistência financeira.

## Estado atual — implementado

- Python 3.12;
- SQLAlchemy e Alembic;
- SQLite para desenvolvimento local;
- User, Account, Category e Subcategory;
- Transaction e Settlement;
- services, repositories e query services;
- cálculos por competência, vencimento e caixa;
- testes automatizados com pytest;
- primeira vertical slice funcional em Streamlit para Movimentações, Contas e Categorias.
- FastAPI com health, cadastros de referência e fluxos HTTP de Transaction,
  Settlement, cancelamento e resumos financeiros.
- foundation React, TypeScript e Vite com HashRouter, layout responsivo,
  Aurora UI v1, cliente HTTP e integração com a API;
- listagem e cadastro web de contas, categorias e subcategorias;
- experiência web de Movimentações com perspectivas, período, filtros,
  paginação, resumos, criação, detalhe, liquidações e cancelamento;
- testes do frontend com Vitest e React Testing Library.

O Streamlit é um protótipo funcional temporário e a referência de equivalência
para a migração web. Ele não receberá novos domínios.

## Arquitetura alvo — planejada

```text
GitHub Pages
↓
React + TypeScript + Vite
↓ HTTPS / JSON
FastAPI (/api/v1)
↓
Services / Query Services
↓
Repositories
↓
SQLAlchemy
↓
SQLite (desenvolvimento) / PostgreSQL (produção)
```

A validação final de equivalência, a autenticação real e o PostgreSQL de
produção ainda não estão implementados. React e FastAPI já cobrem os fluxos da
vertical slice de Contas, Categorias e Movimentações.
GitHub Pages hospedará somente o frontend estático. O backend Python será
hospedado separadamente e consumido por HTTPS.

O projeto permanece em monorepo. O backend existente continua na raiz, com
`api/` e `frontend/` adicionados sem reorganização prematura para um diretório
`backend/`.

## Stack

Implementada:

- Python 3.12;
- Streamlit, temporário;
- SQLAlchemy;
- Alembic;
- SQLite;
- Pandas;
- Plotly;
- pytest.
- FastAPI;
- Uvicorn;
- HTTPX para testes de integração da API.

Planejada:

- PostgreSQL em produção;
- GitHub Pages para o frontend.

Frontend implementado:

- React;
- TypeScript;
- Vite;
- React Router com `HashRouter`;
- CSS próprio com design tokens e Aurora UI v1;
- Lucide React;
- Vitest e React Testing Library.

## Estrutura atual relevante

```text
models/          modelos ORM
repositories/    persistência
services/        regras financeiras e consultas
database/        conexão e migrations
tests/           testes automatizados
pages/           páginas do protótipo Streamlit
components/      componentes do protótipo
utils/           utilitários
docs/            documentação técnica e funcional
app.py           entrada atual do Streamlit
frontend/        aplicação web React/TypeScript/Vite
```

A estrutura futura está descrita em `docs/ARCHITECTURE.md`.

## Requisitos atuais

- Python 3.12 ou versão compatível;
- `pip`;
- Node.js 24 ou versão compatível;
- npm.

## Configuração local atual

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

O padrão utiliza SQLite local:

```dotenv
DATABASE_URL=sqlite:///aurora_finance.db
AURORA_ENV=development
CORS_ALLOWED_ORIGINS=http://localhost:5173
AURORA_DEV_USER_EMAIL=usuario@aurora.local
```

`.env`, bancos pessoais e exports financeiros não devem ser versionados.
`AURORA_DEV_USER_EMAIL` deve corresponder a um usuário ativo já existente; a
API nunca cria esse usuário automaticamente.

## Executar a aplicação atual

```powershell
streamlit run app.py
```

Esse comando inicia somente o protótipo Streamlit existente. Ainda não há
substituição funcional pelo frontend React/Vite.

## Executar o frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

A aplicação estará disponível em `http://localhost:5173/aurora-finance/` e usa
rotas hash. `VITE_API_BASE_URL` é uma configuração pública e não deve conter
segredos. O frontend consome health, contas, categorias, subcategorias,
movimentações, liquidações e resumos financeiros.

Validações do frontend:

```powershell
npm run test
npm run typecheck
npm run build
```

O diretório `dist/` é gerado localmente e não é versionado. A configuração é
compatível com o project site `/aurora-finance/`, mas nenhum deploy ou workflow
de GitHub Pages foi criado.

## Executar a API atual

Depois de aplicar as migrations e configurar um usuário DEV existente:

```powershell
python -m uvicorn api.main:app --reload
```

Health:

```text
GET http://localhost:8000/api/v1/health
```

Endpoints implementados nesta etapa:

- `GET/POST /api/v1/accounts`;
- `GET/POST /api/v1/categories`;
- `GET/POST /api/v1/categories/{category_id}/subcategories`.
- `GET/POST /api/v1/transactions`;
- `GET /api/v1/transactions/{transaction_id}`;
- `POST /api/v1/transactions/settled`;
- `POST /api/v1/transactions/{transaction_id}/settlements`;
- `POST /api/v1/transactions/{transaction_id}/cancellation`;
- `GET /api/v1/transaction-summaries`.

Listagens e resumos exigem `start_date` e `end_date` em ISO 8601 e aceitam as
perspectivas `COMPETENCE`, `DUE` e `CASH`. Autenticação real ainda não existe;
portanto, a API financeira não deve ser publicada na internet.

## Testes

```powershell
python -m pytest
```

Os testes utilizam bancos isolados e não devem acessar o banco pessoal.

## Alembic

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic downgrade -1
```

Uma nova migration só deve ser criada após alteração aprovada nos models:

```powershell
python -m alembic revision --autogenerate -m "descrição da alteração"
```

## Próximo marco

A prioridade atual é **Web Platform Migration**:

1. formalizar a documentação;
2. preparar a camada de aplicação;
3. fundação React/Vite — concluída;
4. reproduzir Contas e Categorias — concluído;
5. reproduzir Movimentações — concluído;
6. validar equivalência funcional — próximo passo;
7. preparar os ambientes de produção;
8. remover Streamlit somente após todos os critérios serem atendidos.

Novos domínios financeiros permanecem bloqueados durante esse marco.

## Segurança básica

- A API financeira não poderá ser publicada sem autenticação adequada.
- CORS não é autenticação.
- Produção exige HTTPS.
- Variáveis `VITE_*` são públicas e nunca podem conter segredos.
- `DATABASE_URL` pertence exclusivamente ao backend.
- O cliente nunca deve escolher `user_id`.
- Stack traces e payloads financeiros completos não devem ser expostos.

Consulte `docs/API_CONTRACTS.md` para os contratos atuais da API.
