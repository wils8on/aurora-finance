# Aurora Finance

Aurora Finance é uma plataforma pessoal de gestão, planejamento e inteligência
financeira. O projeto separa compromissos econômicos (`Transaction`) de eventos
de caixa (`Settlement`) e prioriza rastreabilidade e consistência financeira.

## Estado atual — implementado

- Python 3.12;
- SQLAlchemy e Alembic;
- SQLite para desenvolvimento local;
- PostgreSQL validado como banco compatível para produção;
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
- autenticação própria com Argon2id, sessões opacas server-side, cookie HttpOnly
  e proteção CSRF por token e validação de origem.

O Streamlit é um protótipo funcional temporário e a referência de equivalência
para a migração web. A equivalência funcional e financeira da vertical slice
foi validada; o Streamlit permanece no repositório aguardando decisão explícita
de aposentadoria e não receberá novos domínios.

## Arquitetura de produção — preparada

```text
Browser → HTTPS → edge/roteador gerenciado
                    ├── / e /assets/* → React + TypeScript + Vite
                    └── /api/* → FastAPI (/api/v1)
↓
Services / Query Services
↓
Repositories
↓
SQLAlchemy
↓
SQLite (desenvolvimento) / PostgreSQL (produção)
```

A equivalência funcional e financeira entre Streamlit e React + FastAPI foi
validada, incluindo competência, vencimento, caixa e o dia operacional
`America/Sao_Paulo`. A autenticação real está implementada e o backend foi
validado contra PostgreSQL real; o deploy de produção ainda não foi realizado.
React e FastAPI cobrem os fluxos da vertical slice de Contas, Categorias e
Movimentações.
A decisão para produção é uma única origem pública HTTPS com roteamento por
caminho. GitHub Pages deixa de ser necessário, pois não compõe sozinho
frontend e `/api/*` na mesma origem. Nenhum fornecedor ou deploy foi escolhido.

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
- Argon2-cffi para password hashing Argon2id.
- Psycopg 3, em modo síncrono, para PostgreSQL.

Planejada para implantação:

- PostgreSQL em produção;
- edge/hospedagem estática e backend sob a mesma origem HTTPS.

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
AUTH_SESSION_HOURS=12
AUTH_COOKIE_NAME=aurora_session
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
```

`.env`, bancos pessoais e exports financeiros não devem ser versionados.
Em produção, `AURORA_ENV=production`, `AUTH_COOKIE_SECURE=true` e uma allowlist
HTTPS explícita em `CORS_ALLOWED_ORIGINS` são obrigatórios. O backend falha ao
iniciar se essas garantias não estiverem presentes. Variáveis `VITE_*` são
públicas e nunca devem receber credenciais ou segredos.

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

O diretório `dist/` é gerado localmente e não é versionado. O padrão local
continua compatível com `/aurora-finance/`. No futuro build de produção,
`VITE_BASE_PATH=/` e `VITE_API_BASE_URL=/api/v1` atenderão a origem única.

## Executar a API atual

Depois de aplicar as migrations, provisione explicitamente o primeiro usuário:

```powershell
python -m alembic upgrade head
python -m scripts.provision_user --name "Seu nome" --email voce@example.com
```

A senha é solicitada de forma interativa, deve ter de 12 a 256 caracteres e é
persistida somente como hash Argon2id. Não existe endpoint público de cadastro.
Então inicie a API:

```powershell
python -m uvicorn api.main:app --reload
```

Health:

```text
GET http://localhost:8000/api/v1/health
```

Endpoints implementados nesta etapa:

- `POST /api/v1/auth/login`;
- `GET /api/v1/auth/me`;
- `POST /api/v1/auth/logout`;
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
perspectivas `COMPETENCE`, `DUE` e `CASH`. Todos os endpoints financeiros
exigem sessão autenticada e inferem ownership exclusivamente do usuário da
sessão.

O browser recebe um identificador opaco em cookie `HttpOnly`; somente seu hash
SHA-256 é persistido. Login e toda escrita autenticada exigem `Origin` na
allowlist. Escritas também exigem `X-CSRF-Token`, fornecido por login ou
`/auth/me` e mantido apenas em memória pelo frontend. Logout revoga a sessão no
servidor e remove o cookie. Na topologia de produção same-origin o cookie usa
`SameSite=Lax; Secure`; desenvolvimento local também usa `SameSite=Lax`, sem
`Secure` quando executado por HTTP.

## Testes

```powershell
python -m pytest
```

Os testes utilizam bancos isolados e não devem acessar o banco pessoal.

A validação PostgreSQL é opt-in para manter a suíte cotidiana leve. Ela exige
uma instância PostgreSQL real e uma URL administrativa destinada somente a
testes. A suíte cria um banco com nome aleatório, aplica todas as migrations,
executa os testes e descarta o banco ao terminar:

```powershell
$env:AURORA_TEST_POSTGRES_URL="postgresql+psycopg://USUARIO:SENHA@HOST:5432/postgres"
python -m pytest -m postgresql tests/postgresql
Remove-Item Env:AURORA_TEST_POSTGRES_URL
```

Nunca aponte essa variável para um banco pessoal ou de produção. O valor não
deve ser salvo no `.env` versionado nem exposto ao frontend.

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
6. validar equivalência funcional e financeira — concluído;
7. autenticação browser-first — concluída;
8. validar compatibilidade PostgreSQL — concluído;
9. definir arquitetura e checklist de produção — concluído;
10. implantar e validar o ambiente de produção — próximo passo;
11. decidir explicitamente pela aposentadoria do Streamlit somente após todos os
   critérios de retirada serem atendidos.

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
Consulte também `docs/PRODUCTION_ARCHITECTURE.md` e
`docs/PRODUCTION_CHECKLIST.md` antes de qualquer publicação.
