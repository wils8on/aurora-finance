# Aurora Finance — Arquitetura

## 1. Visão Geral

Aurora Finance é uma aplicação pessoal de gestão, planejamento e
inteligência financeira.

A arquitetura deve privilegiar:

- separação de responsabilidades;
- regras financeiras independentes da interface;
- testabilidade;
- rastreabilidade;
- evolução incremental;
- futura migração de SQLite para PostgreSQL.

A aplicação utiliza inicialmente:

- Python
- Streamlit
- SQLAlchemy
- Alembic
- SQLite
- Pandas
- Plotly

---

## 2. Arquitetura em Camadas

Fluxo padrão:

UI
↓
Service
↓
Repository
↓
ORM
↓
Database

### UI — pages/ e components/

Responsável por:

- apresentação;
- formulários;
- filtros;
- navegação;
- feedback ao usuário.

A UI não deve implementar regras financeiras relevantes.

### Services — services/

Responsável pelas regras de negócio.

Exemplos:

- registrar movimentação;
- realizar pagamento;
- gerar parcelamento;
- gerar recorrências;
- calcular orçamento;
- realizar transferência;
- calcular projeções.

### Repositories — repositories/

Responsável pelo acesso aos dados.

Exemplos:

- buscar movimentações;
- salvar conta;
- consultar categorias;
- persistir parcelas.

Repositories não devem decidir regras financeiras.

### Models — models/

Representação ORM das entidades persistentes.

### Schemas — schemas/

Validação e transporte de dados entre camadas.

---

## 3. Estrutura

aurora-finance/
│
├── app.py
├── assets/
├── components/
├── database/
│ ├── connection.py
│ └── migrations/
├── docs/
├── imports/
├── models/
├── pages/
├── repositories/
├── schemas/
├── services/
├── tests/
├── utils/
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
└── requirements.txt

---

## 4. Dependências entre Camadas

Permitido:

pages → services
services → repositories
repositories → models
models → database

Evitar:

pages → database
pages → SQL direto
pages → repositories quando existir service apropriado
models → pages
repositories → Streamlit
services → Streamlit

O domínio financeiro deve continuar funcional independentemente
da interface Streamlit.

---

## 5. Banco de Dados

Banco inicial:

SQLite

ORM:

SQLAlchemy

Migrations:

Alembic

A aplicação não deve depender de particularidades do SQLite que
impeçam futura migração para PostgreSQL.

IDs devem utilizar estratégia consistente.

Valores monetários devem utilizar Numeric/Decimal.

Datas devem utilizar tipos date/datetime adequados.

---

## 6. Sessões

A criação de sessões SQLAlchemy deve ser centralizada em:

database/connection.py

Não criar engines ou sessões diretamente nas páginas.

---

## 7. Estado Financeiro

O banco armazena fatos financeiros.

Indicadores derivados devem ser calculados sempre que razoável.

Exemplos normalmente calculados:

- saldo atual;
- total mensal;
- resultado mensal;
- comprometimento;
- patrimônio líquido;
- percentual utilizado do orçamento;
- projeções.

Evitar duplicar informação derivável.

---

## 8. Integridade

Relacionamentos financeiros importantes devem utilizar constraints
e foreign keys sempre que aplicável.

Registros utilizados historicamente não devem desaparecer apenas porque
deixaram de ser utilizados.

Preferir arquivamento/desativação para entidades como:

- contas;
- cartões;
- categorias.

---

## 9. Exclusão

Operações financeiras exigem rastreabilidade.

Quando uma movimentação realizada precisar ser corrigida, priorizar
cancelamento/estorno quando a exclusão física comprometer o histórico.

Registros puramente planejados ainda não realizados podem admitir
exclusão conforme regras de negócio.

---

## 10. Evolução

Toda alteração estrutural do banco deve utilizar migration.

Não alterar manualmente banco de produção para acompanhar mudança
de model.

Alterações relevantes devem atualizar:

- DATA_MODEL.md;
- BUSINESS_RULES.md;
- testes correspondentes.

---

## 11. Segurança

Nunca versionar:

- .env;
- bancos pessoais;
- exports financeiros;
- tokens;
- credenciais;
- backups contendo dados reais.

Dados financeiros reais devem permanecer fora do Git.
