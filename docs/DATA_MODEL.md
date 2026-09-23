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

Entidade financeira central.

Campos:

id
user_id
account_id
category_id
subcategory_id

transaction_type
status

description

amount

competence_date
due_date
realized_at

notes

origin_type
origin_id

created_at
updated_at

Tipos:

INCOME
EXPENSE
TRANSFER

Status:

PLANNED
PENDING
REALIZED
CANCELLED

amount deve ser positivo.

O sentido financeiro será determinado por transaction_type.

---

# 6. Transfer

Representa relacionamento de transferência entre contas.

Campos:

id
user_id
source_account_id
destination_account_id
amount
transfer_date
status
notes
created_at
updated_at

Origem e destino não podem ser iguais.

A implementação deverá garantir que transferência não seja contada
como receita/despesa comum.

---

# 7. CreditCard

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

# 8. CardPurchase

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

# 9. CardInstallment

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

# 10. CreditCardInvoice

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

---

# 11. Recurrence

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

---

# 12. InstallmentPlan

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

# 13. Installment

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

---

# 14. Debt

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

# 15. DebtInstallment

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

---

# 16. Budget

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

# 17. BudgetItem

Campos:

id
budget_id
category_id
subcategory_id
planned_amount
created_at
updated_at

---

# 18. Goal

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

# 19. Scenario

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

# 20. ScenarioEvent

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

# 21. InvestmentAccount

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

# 22. InvestmentTransaction

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

---

# Relacionamentos principais

User
├── Account
├── Category
│ └── Subcategory
├── Transaction
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
