# Aurora Finance — Arquitetura

## 1. Estado arquitetural

O núcleo financeiro Python está implementado e deve ser preservado. A interface
Streamlit existente é um protótipo funcional temporário e a referência de
equivalência da migração web.

A apresentação definitiva é React + TypeScript + Vite consumindo FastAPI. A
vertical slice está implementada; o ambiente de produção ainda não foi criado.

## 2. Arquitetura alvo

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

Responsabilidades:

- React apresenta dados e controla interação; não contém regras financeiras oficiais.
- FastAPI é adaptador HTTP; valida e traduz contratos, mas não duplica o domínio.
- Services executam regras de negócio e casos de uso.
- Query services executam leituras, filtros e agregações.
- Repositories encapsulam persistência e não decidem regras financeiras.
- Models representam entidades persistentes.
- SQLAlchemy e Alembic permanecem a camada de persistência e evolução do schema.

## 3. Hospedagem e origem pública

A decisão de produção é usar uma única origem HTTPS com roteamento por caminho:
frontend em `/` e `/assets/*`, API em `/api/*`. GitHub Pages não é necessário
nem recomendado para essa topologia, pois não fornece sozinho essa composição.
O edge pode ser nativo da plataforma; não há exigência de proxy autogerenciado.

A decisão completa está em `PRODUCTION_ARCHITECTURE.md` e os gates de
implantação em `PRODUCTION_CHECKLIST.md`. Provedor e domínio permanecem
deliberadamente não escolhidos.

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
- resolver `current_user` pela sessão autenticada;
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

## 11. Roteamento do frontend

A decisão inicial `HashRouter` permanece por não criar dependência de fallback
SPA. `BrowserRouter` poderá ser reconsiderado depois que o edge demonstrar
fallback confiável; não é requisito para o primeiro deploy.

O `base` do Vite é configurável por `VITE_BASE_PATH`: o padrão atual permanece
`/aurora-finance/` e produção na raiz usará `/`.

## 12. Ambientes e configuração

Desenvolvimento planejado:

- React/Vite: `localhost:5173`;
- FastAPI: `localhost:8000`;
- banco: SQLite local.

Produção planejada:

- origem única HTTPS com frontend estático em `/`;
- FastAPI roteado por `/api/*`;
- PostgreSQL gerenciado e privado quando possível.

`VITE_API_BASE_URL` será `/api/v1` em produção. Toda variável
`VITE_*` é pública. `DATABASE_URL` e demais segredos pertencem somente ao
backend.

## 13. Autenticação e segurança

A estratégia escolhida é autenticação própria: email e senha com hash Argon2id,
sessão opaca persistida no backend e cookie HttpOnly. Ela mantém logout e
revogação sob controle do Aurora, evita expor a credencial de sessão ao
JavaScript e não adiciona dependência operacional de um provedor externo.
OIDC/OAuth permanece uma alternativa futura se a operação multiusuário exigir.

Fluxo:

```text
React → login
→ FastAPI valida Argon2id e cria AuthSession
→ cookie opaco HttpOnly
→ dependência central resolve current_user
→ services/query services
```

Somente o hash SHA-256 do token da sessão é persistido. O token CSRF separado é
mantido em memória pelo frontend e enviado no header `X-CSRF-Token` para
operações inseguras. Essas operações também validam `Origin`; login valida
`Origin` para impedir login CSRF. Logout revoga a sessão no servidor.

O cliente nunca escolhe `user_id`. Não há fallback implícito para usuário de
desenvolvimento nem endpoint público de cadastro. O primeiro usuário é
provisionado por CLI. Na topologia same-origin, produção usa cookie host-only
`Secure; HttpOnly; SameSite=Lax; Path=/api/v1`. `SameSite=None` fica reservado
a uma alternativa realmente cross-site e exige `Secure`.

Regras adicionais:

- CORS usa origens explícitas e não substitui autenticação ou CSRF;
- HTTPS é obrigatório em produção;
- ownership é sempre verificado no backend;
- payloads são validados;
- segredos nunca entram no frontend;
- stack traces não são retornados;
- payload financeiro completo não é logado por padrão;
- bancos reais, exports e credenciais permanecem fora do Git.

## 14. SQLite para PostgreSQL

A compatibilidade do backend foi validada em PostgreSQL 17.11 real e descartável,
com Psycopg 3 síncrono. A execução cobriu todas as migrations históricas em
banco vazio, `alembic check`, schema, autenticação, ownership, Transaction,
Settlement e summaries. SQLite continua sendo o padrão leve de desenvolvimento.

A suíte PostgreSQL é opt-in, marcada com `postgresql`, cria um banco isolado de
nome aleatório e o remove ao final. Ela não usa banco pessoal nem banco futuro
de produção. A aplicação mantém a configuração existente por `DATABASE_URL`;
argumentos específicos de SQLite não são aplicados ao engine PostgreSQL, que
utiliza o pool síncrono padrão do SQLAlchemy.

Matriz de equivalência validada:

| Capacidade | SQLite | PostgreSQL | Resultado |
|---|---|---|---|
| Migrations | validado | validado | EQUIVALENTE |
| Money (`Numeric`/`Decimal`) | validado | validado | EQUIVALENTE |
| Competência | validado | validado | EQUIVALENTE |
| Vencimento | validado | validado | EQUIVALENTE |
| Caixa | validado | validado | EQUIVALENTE |
| Timezone operacional | validado | validado | EQUIVALENTE |
| Settlement parcial | validado | validado | EQUIVALENTE |
| Múltiplos Settlements | validado | validado | EQUIVALENTE |
| Summaries | validado | validado | EQUIVALENTE |
| Autenticação | validado | validado | EQUIVALENTE |
| Sessões | validado | validado | EQUIVALENTE |
| Ownership | validado | validado | EQUIVALENTE |

O caso crítico `2026-09-23T02:30:00Z` foi persistido como `timestamptz` e
classificado no dia operacional `2026-09-22` em `America/Sao_Paulo`. A
Transaction de `90.00` com Settlements de `30.00` e `60.00` preservou total
histórico `90.00`, valores por período e uma única ocorrência por listagem.

Continuam relevantes antes da operação pública:

- timezone;
- enums;
- `SELECT FOR UPDATE`;
- concorrência de liquidações;
- ordenação de `NULL`;
- pesquisa case-insensitive;
- funções SQL usadas pelos query services;
- testes de concorrência real sob a topologia de hospedagem escolhida.

Nenhum provedor PostgreSQL está escolhido e nenhum ambiente de produção foi
configurado. Os índices atuais atendem aos fluxos pessoais esperados; a consulta
de Caixa deve ser reavaliada com `EXPLAIN` somente quando houver volume real que
justifique um índice adicional por `settled_at`.

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
