# Aurora Finance — Contratos da API

Status: implementação parcial
Versão inicial planejada: `/api/v1`

Health, contas, categorias, subcategorias, movimentações, liquidações,
cancelamento e resumos estão implementados. Autenticação real e produção
permanecem planejados.

## 1. Propósito

A API expõe casos de uso e consultas do Aurora Finance por HTTP/JSON. FastAPI
será um adaptador: valida entrada, resolve dependências, chama services/query
services e serializa respostas. Regras financeiras permanecem no domínio.

## 2. Versionamento

Todos os endpoints iniciais usarão o prefixo:

```text
/api/v1
```

Mudanças incompatíveis de contrato exigirão estratégia explícita de versão. A
versão HTTP não altera os valores persistidos dos enums nem a versão do domínio.

## 3. Princípios

- JSON é o formato de transporte.
- Nomes de campos são estáveis e em inglês.
- Enums usam valores canônicos, não rótulos de apresentação.
- Entidades ORM não são contratos públicos.
- O frontend não envia `user_id`; ele vem do futuro `current_user`.
- Ownership é validado no backend.
- Campos derivados são calculados no backend.
- O frontend depende de códigos de erro, não de textos.

## 4. Decimal

Dinheiro é transportado como string decimal canônica:

```json
{
  "amount": "1234.56"
}
```

Fluxo:

```text
JSON string
→ Decimal
→ service
→ Numeric
→ Decimal
→ JSON string
```

Regras:

- separador decimal da API: ponto;
- precisão monetária atual: no máximo duas casas;
- valores devem ser finitos;
- `float` nunca é fonte de verdade financeira;
- `R$ 1.234,56` não é aceito pela API;
- o frontend formata BRL para apresentação.

## 5. Datas

Datas econômicas usam ISO 8601 sem horário:

```json
{
  "competence_date": "2026-09-01",
  "due_date": "2026-09-10"
}
```

`competence_date` e `due_date` representam dimensões econômicas e não devem
ser convertidas entre timezones.

## 6. Timezone e datetime

Timezone operacional: `America/Sao_Paulo`.

Eventos temporais usam ISO 8601 timezone-aware:

```json
{
  "settled_at": "2026-09-23T14:30:00-03:00"
}
```

Política:

- frontend envia offset explícito;
- API rejeita datetime ingênuo;
- backend normaliza o instante para UTC;
- persistência representa corretamente o instante;
- API retorna datetime timezone-aware, preferencialmente UTC;
- frontend apresenta em `America/Sao_Paulo`.

Consultas dependentes de "hoje" usarão uma fonte temporal explícita baseada no
timezone operacional, não `date.today()` nem o timezone acidental do processo.

## 7. Enums

Enums usam valores estáveis, por exemplo:

- `INCOME`, `EXPENSE`;
- `ACTIVE`, `CANCELLED`;
- `PENDING`, `PARTIAL`, `SETTLED`, `CANCELLED`;
- `COMPETENCE`, `DUE`, `CASH`;
- `CHECKING`, `SAVINGS`, `CASH`, `DIGITAL`, `OTHER`.

Rótulos como “Receita”, “Despesa” e “Liquidada” pertencem ao frontend.

## 8. IDs

IDs podem existir nos contratos e inicialmente são inteiros. Não são exibidos
como informação principal ao usuário. Receber um ID não autoriza acesso: todo
recurso é consultado no contexto do usuário autenticado.

## 9. Paginação e filtros

Formato conceitual:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 0,
    "total_pages": 1
  }
}
```

Parâmetros implementados para movimentações:

- `perspective`;
- `start_date`;
- `end_date`;
- `transaction_type`;
- `derived_status`;
- `category_id`;
- `subcategory_id`;
- `search`;
- `include_cancelled`;
- `page`;
- `page_size`.

`start_date` e `end_date` são obrigatórios, o intervalo deve ser crescente e
`page_size` aceita de 1 a 100 itens. A paginação padrão é 25 itens.

## 10. Erros

Formato conceitual:

```json
{
  "error": {
    "code": "SETTLEMENT_EXCEEDS_REMAINING_AMOUNT",
    "message": "A liquidação excede o valor restante.",
    "field": "amount",
    "details": {
      "remaining_amount": "100.00"
    },
    "request_id": "..."
  }
}
```

`field` pode ser `null` e `details` pode ser vazio. O frontend depende de
`code`; `message` é texto humano.

Categorias:

| HTTP | Significado |
|---:|---|
| 422 | payload inválido ou validação semântica |
| 404 | recurso inexistente ou ownership ocultado |
| 409 | conflito ou transição financeira inválida |
| 401 | não autenticado, futuramente |
| 403 | não autorizado, quando aplicável futuramente |
| 500 | erro inesperado |

Exceptions do domínio permanecem independentes de FastAPI e são traduzidas por
handlers da API. Stack traces nunca são enviados ao frontend.

## 11. Sessão e transação

Uma Session SQLAlchemy por request:

```text
abrir
→ executar caso de uso
→ commit único
→ rollback em erro
→ fechar
```

Services podem usar `flush`; repositories não fazem commit. A criação conjunta
de Transaction + Settlement permanece uma única operação atômica.

## 12. Autenticação futura

Autenticação não está implementada e o provedor não foi escolhido.

```text
React
→ credencial, token ou sessão
→ FastAPI
→ current_user
→ services
```

Em desenvolvimento poderá existir `current_user` operacional explicitamente
configurado. Em produção:

- não criar usuário automaticamente;
- não aceitar modo operacional inseguro;
- impedir publicação da API financeira sem autenticação adequada;
- nunca confiar em `user_id` enviado pelo cliente.

CORS não substitui autenticação.

## 13. Endpoints

### Implementados

### Saúde

```text
GET /api/v1/health
```

### Contas

```text
GET  /api/v1/accounts
POST /api/v1/accounts
```

Criação conceitual:

```json
{
  "name": "Conta principal",
  "institution": "Banco",
  "account_type": "CHECKING",
  "initial_balance": "1000.00",
  "initial_balance_date": "2026-09-01"
}
```

### Categorias e subcategorias

```text
GET  /api/v1/categories
POST /api/v1/categories
GET  /api/v1/categories/{category_id}/subcategories
POST /api/v1/categories/{category_id}/subcategories
```

### Movimentações

```text
GET  /api/v1/transactions
GET  /api/v1/transactions/{transaction_id}
POST /api/v1/transactions
POST /api/v1/transactions/settled
POST /api/v1/transactions/{transaction_id}/settlements
POST /api/v1/transactions/{transaction_id}/cancellation
```

Criação pendente:

```json
{
  "transaction_type": "EXPENSE",
  "description": "Aluguel",
  "amount": "1500.00",
  "competence_date": "2026-09-01",
  "due_date": "2026-09-10",
  "category_id": 12,
  "subcategory_id": 31,
  "notes": null
}
```

Settlement:

```json
{
  "account_id": 2,
  "amount": "500.00",
  "settled_at": "2026-09-23T14:30:00-03:00",
  "notes": "Pagamento parcial"
}
```

Criação histórica integral combina os dois payloads em
`POST /api/v1/transactions/settled`, usando `transaction_notes` no nível da
Transaction e o objeto `settlement`. Seu valor deve ser igual ao valor nominal;
a operação inteira sofre rollback se qualquer etapa falhar.

Cancelamento:

```json
{
  "reason": "Cobrança removida"
}
```

Operações específicas são preferíveis a um `PATCH` financeiro genérico, pois
preservam as transições e validações do domínio.

### Resumos

```text
GET /api/v1/transaction-summaries
```

Usa os mesmos filtros da listagem, incluindo `perspective=COMPETENCE`, `DUE` ou
`CASH`. Os campos monetários de resposta são strings. `primary_1`, `primary_2`
e `primary_3` significam, respectivamente:

- competência: receitas, despesas e resultado nominal;
- vencimento: a receber, a pagar e vencido;
- caixa: recebido, pago e fluxo líquido.

Em competência, `receivable` e `payable` também informam os saldos remanescentes.
As agregações são produzidas pelos query services existentes, sem regra
financeira duplicada nas routes.

### Limitação conhecida do SQLite

SQLite não preserva metadados de timezone em `DateTime`. A API normaliza eventos
recebidos para UTC antes da persistência e restitui offset UTC na resposta. A
política permanece compatível com a futura migração para PostgreSQL.
