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

Obrigação financeira conhecida.

### Realizado

Evento financeiro efetivamente ocorrido.

### Projetado

Resultado calculado a partir de fatos, compromissos e hipóteses.

---

## 2. Datas

Uma movimentação pode possuir:

### Data de competência

Período econômico ao qual pertence.

### Data de vencimento

Quando a obrigação deve ser paga ou recebida.

### Data de realização

Quando efetivamente ocorreu financeiramente.

Essas datas não são intercambiáveis.

Relatórios devem declarar qual perspectiva temporal utilizam.

---

## 3. Regime de Caixa e Competência

O Aurora deve suportar análises por:

- competência;
- caixa.

Exemplo:

Compra realizada em setembro e paga em outubro.

Competência:
setembro.

Caixa:
outubro.

A interface deverá deixar claro qual visão está sendo utilizada.

---

## 4. Status de Movimentação

Status iniciais:

- PLANEJADO
- PENDENTE
- REALIZADO
- CANCELADO

PLANEJADO:
intenção ainda não convertida em obrigação.

PENDENTE:
obrigação existente ainda não liquidada.

REALIZADO:
financeiramente liquidado.

CANCELADO:
não deverá ocorrer ou foi invalidado.

Status adicionais só devem ser criados mediante necessidade comprovada.

---

## 5. Contas

Uma conta representa local de recursos financeiros.

Exemplos:

- conta corrente;
- carteira;
- conta digital;
- dinheiro.

Conta pode possuir saldo inicial.

Saldo calculado:

saldo inicial

- receitas realizadas

* despesas realizadas

- transferências recebidas

* transferências enviadas

Não armazenar saldo atual como fonte independente da verdade.

---

## 6. Transferências

Transferência deve possuir origem e destino.

Exemplo:

Banco do Brasil → Nubank

Não contabilizar:

despesa no BB

- receita no Nubank.

Isso inflaria artificialmente receitas e despesas.

---

## 7. Cartões de Crédito

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

---

## 8. Parcelamentos

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

## 9. Recorrências

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

## 10. Categorias

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

## 11. Orçamento

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

---

## 12. Dívidas

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

---

## 13. Investimentos

Transferência de dinheiro de conta corrente para investimento não deve
ser automaticamente interpretada como despesa de consumo.

Investimentos pertencem à composição patrimonial.

A modelagem detalhada será implementada em versão posterior.

---

## 14. Patrimônio

Conceitualmente:

Patrimônio líquido =
ativos

- passivos

A definição exata dos ativos e passivos considerados deve permanecer
documentada conforme novos módulos forem implementados.

---

## 15. Cenários

Cenário é hipotético.

Dados de cenário nunca podem alterar automaticamente dados reais.

Exemplo:

Adicionar hipoteticamente receita mensal de R$ 4.000.

O evento existe apenas dentro daquele cenário.

---

## 16. Projeção

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

## 17. Estornos e Cancelamentos

Uma movimentação realizada não deve simplesmente desaparecer quando
isso prejudicar a rastreabilidade.

Quando apropriado, utilizar operação de estorno vinculada ao lançamento
original.

Cancelamento não é igual a pagamento ou recebimento.

---

## 18. Precisão

Valores monetários devem utilizar Decimal.

Nunca depender de float para cálculos financeiros críticos.

Arredondamento monetário padrão:

2 casas decimais.

Casos especiais deverão possuir regra documentada.
