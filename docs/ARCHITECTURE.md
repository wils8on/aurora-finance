# Aurora Finance — Arquitetura

## 1. Estado arquitetural

O núcleo financeiro Python está implementado e deve ser preservado. A interface
Streamlit existente é um protótipo funcional temporário e a referência de
equivalência da migração web.

A arquitetura definitiva de apresentação será React + TypeScript + Vite,
consumindo uma API FastAPI. Esses componentes ainda estão planejados e não
existem no repositório.

## 2. Arquitetura alvo

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

Responsabilidades:

- React apresenta dados e controla interação; não contém regras financeiras oficiais.
- FastAPI é adaptador HTTP; valida e traduz contratos, mas não duplica o domínio.
- Services executam regras de negócio e casos de uso.
- Query services executam leituras, filtros e agregações.
- Repositories encapsulam persistência e não decidem regras financeiras.
- Models representam entidades persistentes.
- SQLAlchemy e Alembic permanecem a camada de persistência e evolução do schema.

## 3. GitHub Pages

GitHub Pages hospedará exclusivamente o frontend estático compilado. Não
executa Python, FastAPI, SQLAlchemy, Alembic, migrations, SQLite ou qualquer
banco do backend.

O backend será hospedado separadamente, em HTTPS. O frontend consumirá a URL
pública da API. A implantação do backend e a escolha do provedor permanecem
decisões futuras.

## 4. Monorepo e estrutura

O projeto permanece em monorepo. Para evitar movimentação sem benefício, o
backend Python continua na raiz. Não criar `backend/` sem decisão posterior.

Estrutura conceitual futura:

```text
aurora-finance/
├── api/
│   ├── main.py
│   ├── dependencies/
│   ├── errors/
│   ├── routes/
│   └── schemas/
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── features/
│       ├── layouts/
│       ├── pages/
│       ├── routes/
│       ├── types/
│       ├── utils/
│       └── styles/
├── models/
├── repositories/
├── services/
├── database/
├── tests/
├── pages/          # Streamlit temporário
├── components/     # Streamlit temporário
└── app.py          # Streamlit temporário
```

Os diretórios `api/` e `frontend/` são planejados; não estão implementados.

## 5. Dependências permitidas

```text
frontend → HTTP/JSON
api routes → schemas/dependencies → services/query services
services → repositories
query services → models/SQLAlchemy para leitura
repositories → models
models → database
```

Evitar:

- frontend acessando banco ou contendo cálculos financeiros oficiais;
- routes implementando regras financeiras;
- repositories fazendo commit ou contendo regras complexas;
- services dependendo de FastAPI, React ou Streamlit;
- ORM sendo exposto diretamente como contrato HTTP;
- duplicação das consultas de competência, vencimento e caixa.

## 6. API

A API planejada usará o prefixo `/api/v1`. A camada FastAPI será responsável
por:

- validar payload e parâmetros;
- obter a Session do request;
- resolver o futuro `current_user`;
- converter contratos HTTP em tipos do domínio;
- chamar services ou query services;
- serializar respostas;
- traduzir exceptions do domínio;
- aplicar CORS;
- nunca retornar stack trace.

Os contratos conceituais estão em `docs/API_CONTRACTS.md`.

## 7. Sessão e transação

Cada request terá uma Session SQLAlchemy exclusiva:

```text
abrir
→ executar caso de uso
→ commit único
→ rollback em erro
→ fechar
```

Services podem usar `flush`, mas não devem assumir commits arbitrários.
Repositories não fazem commit. A operação composta Transaction + Settlement
deve permanecer atômica.

## 8. Dinheiro

Internamente, valores monetários continuam como `Decimal` e `Numeric`. Na
fronteira HTTP são strings decimais canônicas:

```text
JSON string → Decimal → service → Numeric
Numeric → Decimal → JSON string
```

O frontend formata BRL. `float` não é fonte de verdade financeira.

## 9. Datas e timezone

Timezone operacional: `America/Sao_Paulo`.

- `competence_date` e `due_date` são datas econômicas sem horário;
- eventos como `settled_at`, `cancelled_at`, `created_at` e `updated_at`
  são timezone-aware;
- o frontend envia ISO 8601 com offset;
- a API rejeita datetime ingênuo;
- o backend normaliza eventos para UTC;
- a API retorna ISO 8601 timezone-aware, preferencialmente UTC;
- o frontend apresenta em `America/Sao_Paulo`.

Consultas dependentes de data atual deverão utilizar uma fonte temporal
explícita baseada nessa política. Não devem depender do timezone acidental do
processo nem de `date.today()`.

## 10. Frontend e design system

A aplicação React será organizada por features, sem complexidade desnecessária.
Nenhuma biblioteca visual está escolhida.

O design system partirá de:

- tokens de cor;
- tipografia;
- espaçamento;
- radius;
- sombras;
- estados interativos;
- responsividade;
- acessibilidade.

Rotas iniciais:

- `/` ou entrada equivalente;
- `/movimentacoes`;
- `/contas`;
- `/categorias`.

A estrutura não deve bloquear módulos futuros, mas eles não serão antecipados.

## 11. Roteamento no GitHub Pages

A decisão inicial é `HashRouter`, por funcionar com refresh direto no GitHub
Pages sem rewrite de servidor. `BrowserRouter` poderá ser reconsiderado quando
houver hospedagem com fallback SPA apropriado.

O `base` do Vite deverá refletir o nome real e a capitalização real do
repositório no momento do deploy. Não há valor fixado nesta documentação.

## 12. Ambientes e configuração

Desenvolvimento planejado:

- React/Vite: `localhost:5173`;
- FastAPI: `localhost:8000`;
- banco: SQLite local.

Produção planejada:

- frontend: GitHub Pages;
- backend: host HTTPS separado;
- banco: PostgreSQL.

`VITE_API_BASE_URL` poderá conter a URL pública da API. Toda variável
`VITE_*` é pública. `DATABASE_URL` e demais segredos pertencem somente ao
backend.

## 13. Autenticação e segurança

Autenticação real ainda não está implementada nem teve provedor escolhido.
A API financeira não poderá ser publicada na internet sem autenticação
adequada.

Fluxo futuro:

```text
React
→ credencial, token ou sessão
→ FastAPI
→ current_user
→ services
```

O cliente nunca escolhe `user_id`. Em desenvolvimento local poderá existir um
usuário operacional explicitamente configurado. Produção deve impedir criação
automática de usuário e qualquer modo operacional inseguro.

Regras adicionais:

- CORS usa origens explícitas e não é autenticação;
- HTTPS é obrigatório em produção;
- ownership é sempre verificado no backend;
- payloads são validados;
- segredos nunca entram no frontend;
- stack traces não são retornados;
- payload financeiro completo não é logado por padrão;
- bancos reais, exports e credenciais permanecem fora do Git.

## 14. SQLite para PostgreSQL

A evolução preservará SQLAlchemy, Alembic, `Numeric`, `Decimal`, constraints
e migrations. Antes da produção deverão ser validados:

- timezone;
- enums;
- `SELECT FOR UPDATE`;
- concorrência de liquidações;
- ordenação de `NULL`;
- pesquisa case-insensitive;
- funções SQL usadas pelos query services;
- execução integral das migrations em PostgreSQL limpo.

Nenhum provedor PostgreSQL está escolhido.

## 15. Streamlit temporário

O Streamlit permanece congelado como baseline. Só será removido quando React +
FastAPI reproduzirem:

- contas;
- categorias e subcategorias;
- criação de movimentação;
- criação já liquidada;
- listagem, filtros, paginação e detalhe;
- Settlement parcial e integral;
- cancelamento e seu bloqueio após liquidação;
- competência, vencimento e caixa;
- estados vazios, erros e formatação pt-BR;
- resultados financeiros equivalentes.

Também são requisitos: autenticação de produção, frontend publicado, backend
seguro e documentação atualizada.

## 16. Estado financeiro preservado

A migração não altera o domínio:

- Transaction representa obrigação ou fato econômico;
- Settlement representa liquidação e efeito de caixa;
- estados de liquidação permanecem derivados;
- Transfer permanece entidade futura separada;
- valores derivados não devem ser persistidos apenas para a interface;
- correções financeiras preservam rastreabilidade.

Regras completas permanecem em `BUSINESS_RULES.md` e `DATA_MODEL.md`.
