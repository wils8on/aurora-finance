# Aurora Finance — Modelo de Dados

Status: PROPOSTA INICIAL
Versão: 0.1

O modelo será evoluído através de migrations.

---

# 1. User

Preparado para futura expansão multiusuário.

Campos:

id
name
email
currency
is_active
created_at
updated_at

Inicialmente haverá apenas um usuário operacional.

---

# 2. Account

Representa contas financeiras.

Campos:

id
user_id
name
institution
account_type
initial_balance
initial_balance_date
is_active
created_at
updated_at

Tipos iniciais:

CHECKING
SAVINGS
CASH
DIGITAL
OTHER

---

# 3. Category

Campos:

id
user_id
name
type
is_active
created_at
updated_at

type:

INCOME
EXPENSE

---

# 4. Subcategory

Campos:

id
category_id
name
is_active
created_at
updated_at

---

# 5. Transaction

Representa uma obrigação financeira identificável ou um fato econômico de
receita/despesa.

Não representa orçamento genérico, projeção, cenário, transferência entre
contas próprias, pagamento de fatura como nova despesa ou simples
transferência patrimonial.

Campos:

id
user_id
category_id
subcategory_id

transaction_type
status

description

amount

competence_date
due_date

cancelled_at
cancellation_reason

notes

created_at
updated_at

Tipos:

INCOME
EXPENSE

Estados de controle persistidos:

ACTIVE
CANCELLED

amount é o valor econômico nominal da obrigação ou fato financeiro, deve
utilizar Numeric/Decimal e ser positivo.

O sentido financeiro será determinado por transaction_type.

ACTIVE indica apenas que a Transaction pode receber Settlements. Os estados
conceituais de liquidação são derivados, não persistidos:

- PENDING: settled_amount = 0;
- PARTIAL: 0 < settled_amount < Transaction.amount;
- SETTLED: settled_amount = Transaction.amount;
- CANCELLED: cancelamento persistido, permitido somente sem Settlement.

subcategory_id é opcional. category_id é obrigatório e deve possuir tipo
compatível com transaction_type.

Transaction isoladamente não afeta saldo de conta.

O relacionamento de estorno deve preservar o fato original, permitir estorno
parcial futuro e impedir estorno superior ao valor liquidado. Como o efeito de
caixa reside em Settlement, um relacionamento específico entre eventos de
liquidação é preferível a `reverses_transaction_id` isolado. A estrutura exata
será definida antes da implementação de estornos na v0.2.

Relacionamentos de origem devem ser explícitos. `origin_type + origin_id` não
será utilizado como estratégia principal.

---

# 6. Settlement

Representa uma liquidação financeira efetiva de uma Transaction.

Campos:

id
transaction_id
account_id
amount
settled_at
notes
created_at
updated_at

Regras:

- transaction_id e account_id são obrigatórios;
- amount utiliza Numeric/Decimal e deve ser positivo;
- settled_at é obrigatório;
- uma Transaction pode possuir zero, um ou vários Settlements;
- um Settlement pertence a exatamente uma Transaction;
- Settlement afeta o saldo da Account;
- a soma dos Settlements não pode exceder Transaction.amount, salvo regra
  futura explicitamente documentada;
- liquidações parciais são permitidas.

Valores derivados e não armazenados:

settled_amount = SUM(Settlement.amount)

remaining_amount = Transaction.amount - settled_amount

O cadastro ou importação de movimentação histórica já liquidada deve criar
Transaction e Settlement atomicamente, sem inventar expectativa anterior.

---

# 7. Transfer

Representa relacionamento de transferência entre contas.

Campos:

id
user_id
source_account_id
destination_account_id
amount
transferred_at
status
notes
created_at
updated_at

Origem e destino não podem ser iguais. amount deve ser positivo. A operação
deve reduzir a conta de origem e aumentar a conta de destino atomicamente.

A implementação deverá garantir que transferência não seja contada
como receita/despesa comum e não altere o resultado econômico.

Os estados ou mecanismo equivalente de execução de Transfer serão definidos
antes de sua implementação na v0.2.

---

# 8. CreditCard

Campos:

id
user_id
name
institution
credit_limit
closing_day
due_day
is_active
created_at
updated_at

---

# 9. CardPurchase

Campos:

id
user_id
credit_card_id
category_id
subcategory_id

description
total_amount
purchase_date

installment_count

created_at
updated_at

Uma compra pode gerar uma ou várias parcelas.

---

# 10. CardInstallment

Campos:

id
card_purchase_id
installment_number
amount
competence_date
invoice_id
status
created_at
updated_at

---

# 11. CreditCardInvoice

Campos:

id
credit_card_id
reference_month
closing_date
due_date
status
created_at
updated_at

Status possíveis:

OPEN
CLOSED
PAID
CANCELLED

O total da fatura deve ser calculado a partir dos itens relacionados
sempre que possível.

Decisões pendentes antes da implementação do módulo:

- se CardInstallment gerará Transaction;
- como o pagamento da fatura produzirá efeito de caixa;
- como impedir dupla contabilização entre compra, parcela e pagamento.

---

# 12. Recurrence

Campos:

id
user_id
description
transaction_type
account_id
category_id
subcategory_id

amount
frequency
start_date
end_date

is_active
created_at
updated_at

Frequências iniciais:

WEEKLY
MONTHLY
YEARLY

A materialização futura deve utilizar relacionamento explícito, como
RecurrenceOccurrence -> Transaction. Alterar a regra não pode reescrever
Transactions ou Settlements históricos.

---

# 13. InstallmentPlan

Utilizado para parcelamentos que não pertencem necessariamente
a cartão de crédito.

Campos:

id
user_id
description
total_amount
installment_count
first_due_date
created_at
updated_at

---

# 14. Installment

Campos:

id
installment_plan_id
transaction_id
installment_number
amount
due_date
status
created_at
updated_at

Installment deve manter relacionamento explícito com Transaction. Não usar
identificador polimórfico de origem.

---

# 15. Debt

Campos:

id
user_id
creditor
description

original_amount
contract_date

interest_rate
installment_count

status

created_at
updated_at

O saldo devedor não deve ser duplicado sem necessidade quando puder
ser calculado com segurança.

---

# 16. DebtInstallment

Campos:

id
debt_id
installment_number

due_date
principal_amount
interest_amount
fee_amount
total_amount

paid_at
status

created_at
updated_at

A implementação futura deve distinguir principal, juros, encargos,
obrigação e liquidação. Pagamento de principal não é automaticamente
despesa de consumo.

---

# 17. Budget

Campos:

id
user_id
year
month
name
created_at
updated_at

Constraint sugerida:

user_id + year + month + name

---

# 18. BudgetItem

Campos:

id
budget_id
category_id
subcategory_id
planned_amount
created_at
updated_at

BudgetItem representa intenção ou limite agregado. Não deve gerar
Transaction apenas por existir.

---

# 19. Goal

Implementação futura.

Campos previstos:

id
user_id
name
target_amount
target_date
status
created_at
updated_at

---

# 20. Scenario

Implementação futura.

Campos:

id
user_id
name
description
is_active
created_at
updated_at

---

# 21. ScenarioEvent

Campos:

id
scenario_id

event_type
description
amount

start_date
end_date
frequency

created_at
updated_at

Eventos de cenário nunca modificam Transaction.

---

# 22. InvestmentAccount

Implementação futura.

Campos previstos:

id
user_id
name
institution
is_active
created_at
updated_at

---

# 23. InvestmentTransaction

Implementação futura.

Campos previstos:

id
investment_account_id
transaction_type
asset
quantity
unit_price
fees
transaction_date
created_at
updated_at

Aporte não é automaticamente despesa e resgate não é automaticamente
receita. Movimentações patrimoniais devem permanecer separadas do resultado
econômico. Rendimentos, taxas e impostos podem possuir naturezas econômicas
próprias.

---

# Relacionamentos principais

User
├── Account
├── Category
│ └── Subcategory
├── Transaction
│ └── Settlement
├── Transfer
├── CreditCard
│ ├── CardPurchase
│ │ └── CardInstallment
│ └── CreditCardInvoice
├── Recurrence
├── InstallmentPlan
│ └── Installment
├── Debt
│ └── DebtInstallment
├── Budget
│ └── BudgetItem
├── Goal
├── Scenario
│ └── ScenarioEvent
└── InvestmentAccount
└── InvestmentTransaction

---

# Convenções

IDs:
inteiros inicialmente.

Valores monetários:
Numeric / Decimal.

Datas:
date quando horário não possuir significado.

Timestamps:
datetime.

Timestamps técnicos:

created_at
updated_at

Soft state:

is_active

para cadastros que precisam preservar histórico.

---

# Observação

Este documento descreve o domínio completo previsto.

A existência de uma entidade neste documento NÃO significa que ela
deva ser implementada na v0.1.

Consultar ROADMAP.md.
