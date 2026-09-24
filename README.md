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
- FastAPI foundation com health e APIs de contas, categorias e subcategorias.

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

React/Vite, autenticação real, endpoints financeiros e PostgreSQL de produção
ainda não estão implementados. A fundação FastAPI e os endpoints de cadastros
de referência já estão disponíveis.
GitHub Pages hospedará somente o frontend estático. O backend Python será
hospedado separadamente e consumido por HTTPS.

O projeto continuará em monorepo. O backend existente permanece na raiz; serão
adicionados futuramente `api/` e `frontend/`, sem reorganização prematura para
um diretório `backend/`.

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

- React;
- TypeScript;
- Vite;
- PostgreSQL em produção;
- GitHub Pages para o frontend.

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
```

A estrutura futura está descrita em `docs/ARCHITECTURE.md`.

## Requisitos atuais

- Python 3.12 ou versão compatível;
- `pip`.

Node.js não é requisito ainda porque o frontend React/Vite não foi criado.

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
frontend React/Vite.

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

Transaction, Settlement, summaries e autenticação real ainda não são expostos
pela API.

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
3. ampliar a API com os fluxos financeiros após validar a fundação atual;
4. criar a fundação React/Vite;
5. reproduzir Contas, Categorias e Movimentações;
6. validar equivalência funcional;
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

Consulte `docs/API_CONTRACTS.md` para os contratos planejados da API.
