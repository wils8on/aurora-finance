# Aurora Finance — Regras de Negócio

## 1. Conceitos

### Receita

Entrada de recurso financeiro.

### Despesa

Saída de recurso financeiro.

### Transferência

Movimentação entre contas pertencentes ao usuário.

Transferência não representa receita nem despesa patrimonial por si só.

### Orçado

Valor planejado.

### Comprometido

Obrigação financeira identificável, representada por Transaction.

### Realizado

Liquidação financeira efetivamente ocorrida, representada por Settlement.

### Projetado

Resultado calculado a partir de fatos, compromissos e hipóteses.

---

## 2. Datas

Uma Transaction pode possuir:

### Data de competência

Período econômico ao qual pertence.

### Data de vencimento

Quando a obrigação deve ser paga ou recebida.

### Data de liquidação

Registrada em Settlement.settled_at, indica quando o movimento de caixa
efetivamente ocorreu.

Essas datas não são intercambiáveis.

Relatórios devem declarar qual perspectiva temporal utilizam.

---

## 3. Regime de Caixa e Competência

O Aurora deve suportar análises por:

- competência;
- caixa.

Exemplo:

Despesa com competência em setembro, vencimento em outubro e pagamento em
novembro.

Competência:
setembro.

Caixa:
novembro.

A visão por competência utiliza Transaction.competence_date.

A visão de caixa utiliza Settlement.settled_at.

Uma Transaction sem Settlement não integra a visão de caixa.

A interface deverá deixar claro qual visão está sendo utilizada.

---

## 4. Estado de Transaction

Transaction não representa intenção genérica. Por isso, não existe estado
PLANNED em Transaction.

Estados de controle persistidos:

- ACTIVE
- CANCELLED

ACTIVE indica que a Transaction pode receber Settlements. Não informa o grau
de liquidação.

CANCELLED representa obrigação invalidada antes de qualquer liquidação.

Os estados conceituais PENDING, PARTIAL e SETTLED devem ser derivados para
evitar redundância:

- PENDING: soma dos Settlements igual a zero;
- PARTIAL: soma dos Settlements maior que zero e menor que Transaction.amount;
- SETTLED: soma dos Settlements igual a Transaction.amount.

Lifecycle conceitual:

- sem Settlement: PENDING;
- liquidação parcial: PARTIAL derivado;
- liquidação total: SETTLED derivado;
- cancelamento sem Settlement: CANCELLED.

Uma Transaction com qualquer Settlement não pode ser simplesmente cancelada
ou apagada. Correções devem preservar o fato original e utilizar operações
compensatórias.

## 5. Transaction e Settlement

Transaction representa a dimensão econômica ou uma obrigação financeira
identificável. Seu amount é o valor nominal da obrigação ou fato econômico,
sempre positivo. O sentido é definido por INCOME ou EXPENSE.

Settlement representa uma liquidação financeira efetiva associada a uma
Transaction e a uma Account. Uma Transaction pode possuir zero, um ou vários
Settlements, permitindo liquidações parciais.

Valores derivados:

settled_amount = SUM(Settlement.amount)

remaining_amount = Transaction.amount - settled_amount

Esses valores não devem ser armazenados. A soma das liquidações não pode
exceder o valor nominal, salvo regra futura explicitamente documentada.

O cadastro ou importação de histórico já liquidado deve criar Transaction e
Settlement de forma atômica. Não se deve inventar expectativa ou estado
anterior retroativo.

Exemplo de despesa histórica de R$ 125:

- Transaction EXPENSE com amount de R$ 125;
- Settlement de R$ 125 na conta correspondente e com a data real conhecida.

---

## 6. Contas

Uma conta representa local de recursos financeiros.

Exemplos:

- conta corrente;
- carteira;
- conta digital;
- dinheiro.

Conta pode possuir saldo inicial.

Saldo calculado conceitualmente:

```text
saldo inicial
+ Settlements de receitas
- Settlements de despesas
+ Transfers recebidas
- Transfers enviadas
+ demais eventos patrimoniais explicitamente suportados no futuro
```

Não armazenar saldo atual como fonte independente da verdade.

Transaction sem Settlement não altera saldo.

---

## 7. Transferências

Transferência deve possuir origem e destino.

Exemplo:

Banco do Brasil → Nubank

Não contabilizar:

despesa no BB

- receita no Nubank.

Isso inflaria artificialmente receitas e despesas.

Transfer é entidade própria, deve possuir origem e destino diferentes, valor
positivo e execução atômica. Reduz o saldo da origem, aumenta o saldo do
destino e não altera o resultado econômico.

---

## 8. Cartões de Crédito

Cartão não é categoria de despesa.

Compra:

Categoria:
Alimentação

Subcategoria:
Restaurante

Meio:
Cartão Nubank

A compra afeta análise de consumo conforme sua competência.

O pagamento da fatura representa liquidação financeira da obrigação,
não uma segunda despesa de consumo.

Evitar dupla contabilização.

A arquitetura final do módulo permanece pendente. Antes de implementá-lo,
deverá ser decidido:

- se CardInstallment gerará Transaction;
- como o pagamento da fatura produzirá efeito de caixa;
- como compra, parcela e pagamento serão conciliados sem duplicidade.

---

## 9. Parcelamentos

Compra parcelada deve possuir:

- registro de origem;
- número de parcelas;
- valor total;
- parcelas relacionadas.

Parcelas não devem existir como registros independentes sem vínculo
com sua origem.

Diferenças de centavos decorrentes de divisão devem ser tratadas de
forma determinística.

A soma das parcelas deve ser igual ao valor total.

---

## 10. Recorrências

Recorrência representa regra geradora.

Exemplos:

- salário mensal;
- aluguel;
- academia;
- assinatura.

Alterar uma recorrência não deve modificar silenciosamente movimentações
históricas já realizadas.

Alterações podem afetar ocorrências futuras conforme decisão explícita.

---

## 11. Categorias

Categoria representa natureza financeira.

Exemplos:

Moradia
Alimentação
Saúde
Transporte
Educação
Lazer

Subcategoria detalha a categoria.

Instituições financeiras e cartões não devem substituir categorias.

Categorias utilizadas historicamente devem preferencialmente ser
desativadas, não excluídas.

---

## 12. Orçamento

Orçamento deve ser definido por período e categoria/subcategoria.

Permitir comparação:

Orçado
Comprometido
Realizado

Exemplo:

Alimentação

Orçado: R$ 1.000
Comprometido: R$ 600
Realizado: R$ 450

BudgetItem representa intenção ou limite agregado. Transaction representa
obrigação ou fato econômico identificável. Settlement representa liquidação
financeira. Projetado é resultado calculado. Esses conceitos não são
intercambiáveis.

---

## 13. Dívidas

Dívida representa obrigação financeira estruturada.

Pode possuir:

- credor;
- principal;
- saldo devedor;
- juros;
- parcelas;
- pagamentos;
- vencimentos.

Pagamento de dívida pode conter componentes diferentes:

- principal;
- juros;
- encargos.

Quando disponíveis, esses componentes devem ser distinguíveis.

A futura implementação deve distinguir principal, juros, encargos, obrigação
e liquidação. Pagamento de principal não deve ser automaticamente tratado
como despesa de consumo.

---

## 14. Investimentos

Transferência de dinheiro de conta corrente para investimento não deve
ser automaticamente interpretada como despesa de consumo.

Investimentos pertencem à composição patrimonial.

Aporte não é automaticamente despesa e resgate não é automaticamente
receita. Movimentações patrimoniais devem permanecer separadas do resultado
econômico. Rendimentos, taxas e impostos podem possuir naturezas econômicas
próprias.

A modelagem detalhada será implementada em versão posterior.

---

## 15. Patrimônio

Conceitualmente:

Patrimônio líquido =
ativos

- passivos

A definição exata dos ativos e passivos considerados deve permanecer
documentada conforme novos módulos forem implementados.

---

## 16. Cenários

Cenário é hipotético.

Dados de cenário nunca podem alterar automaticamente dados reais.

Exemplo:

Adicionar hipoteticamente receita mensal de R$ 4.000.

O evento existe apenas dentro daquele cenário.

---

## 17. Projeção

Projeção pode considerar:

- saldo atual;
- receitas recorrentes;
- despesas recorrentes;
- parcelas futuras;
- dívidas;
- compromissos;
- eventos de cenário.

Toda projeção deve informar suas premissas.

---

## 18. Estornos e Cancelamentos

Uma movimentação realizada não deve simplesmente desaparecer quando
isso prejudicar a rastreabilidade.

O estorno deve ser uma operação financeira compensatória, vinculada
explicitamente ao evento original. O registro original permanece preservado.

Como o efeito de caixa reside em Settlement, a modelagem definitiva do
estorno deve relacionar liquidações compensatórias às liquidações originais.
Um relacionamento específico de estorno é preferível a depender apenas de
Transaction.reverses_transaction_id.

O desenho deve permitir estorno parcial no futuro e impedir que o total
estornado exceda o valor efetivamente liquidado. A estrutura exata da entidade
ou relacionamento de estorno será definida antes da implementação do fluxo de
estornos na v0.2.

Cancelamento não é igual a pagamento ou recebimento.

---

## 19. Relacionamentos de origem

Relacionamentos explícitos devem substituir `origin_type + origin_id` como
estratégia principal.

Exemplos futuros:

- Installment -> Transaction;
- RecurrenceOccurrence -> Transaction;
- CardInstallment -> relacionamento financeiro definido pelo domínio;
- DebtInstallment -> relacionamento explícito;
- ImportItem -> Transaction.

---

## 20. Precisão

Valores monetários devem utilizar Decimal.

Nunca depender de float para cálculos financeiros críticos.

Arredondamento monetário padrão:

2 casas decimais.

Casos especiais deverão possuir regra documentada.
