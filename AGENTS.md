# AGENTS.md — Aurora Finance

## 1. Propósito

Aurora Finance é uma plataforma pessoal de gestão, planejamento e
inteligência financeira.

O sistema deve permitir compreender:

- onde o dinheiro está;
- de onde veio;
- para onde foi;
- quais compromissos financeiros já existem;
- qual é a situação patrimonial atual;
- como decisões presentes afetam períodos futuros.

O produto não deve ser tratado apenas como um controle de despesas.
Planejamento financeiro e projeção futura são funcionalidades centrais.

---

## 2. Princípios do Produto

1. O banco de dados é a fonte principal da verdade.
2. Anos e meses são dimensões temporais, nunca estruturas físicas separadas.
3. Não criar tabelas específicas para anos.
4. Evitar armazenar valores derivados quando puderem ser calculados com
   segurança a partir dos dados primários.
5. Diferenciar claramente orçamento, compromisso, realização e projeção.
6. Toda movimentação financeira deve possuir rastreabilidade.
7. Recorrências e parcelamentos devem possuir entidades de origem.
8. O sistema deve permanecer utilizável mesmo sem integrações externas.
9. A arquitetura deve permitir futura migração de SQLite para PostgreSQL.
10. Priorizar consistência financeira sobre conveniência de interface.

---

## 3. Stack Principal

- Python
- Streamlit
- SQLAlchemy
- Alembic
- SQLite
- Pandas
- Plotly
- Git
- GitHub

SQLite será utilizado inicialmente.

A camada de persistência não deve depender de comportamentos exclusivos
do SQLite que dificultem futura migração para PostgreSQL.

---

## 4. Arquitetura

Separar responsabilidades entre:

### models/

Modelos ORM e entidades persistentes.

### schemas/

Objetos de entrada, validação e transferência de dados.

### repositories/

Acesso e persistência de dados.

Repositories não devem conter regras de negócio complexas.

### services/

Regras de negócio e operações financeiras.

Cálculos financeiros importantes devem ficar nesta camada, e não
diretamente nas páginas Streamlit.

### pages/

Interface e navegação.

Páginas não devem acessar diretamente o banco quando houver repository
ou service apropriado.

### components/

Componentes visuais reutilizáveis.

### database/

Configuração da conexão, sessão e migrations.

### utils/

Funções utilitárias genéricas.

Não colocar regras financeiras relevantes em utils.

### tests/

Testes automatizados.

### docs/

Documentação funcional e técnica.

---

## 5. Domínios Principais

A arquitetura deve comportar:

- Usuários
- Contas
- Cartões de crédito
- Categorias
- Subcategorias
- Movimentações
- Liquidações
- Recorrências
- Parcelamentos
- Faturas
- Dívidas
- Parcelas de dívidas
- Orçamentos
- Itens de orçamento
- Investimentos
- Movimentações de investimentos
- Metas
- Cenários
- Eventos de cenário

Nem todos precisam ser implementados na primeira versão.

---

## 6. Conceitos Financeiros

### Previsto

Valor planejado no orçamento.

Exemplo:

Pretendo gastar R$ 500 com alimentação em outubro.

### Comprometido

Obrigação financeira conhecida e já assumida.

Exemplo:

Existe uma parcela de R$ 300 vencendo em outubro.

### Realizado

Liquidação financeira efetivamente ocorrida.

Exemplo:

A parcela foi paga.

### Projetado

Valor calculado pelo sistema utilizando dados atuais e hipóteses.

Exemplo:

Saldo estimado para dezembro considerando receitas e compromissos futuros.

Esses conceitos NÃO devem ser tratados como sinônimos.

---

## 7. Movimentações

Transaction é uma das entidades centrais do sistema e representa uma
obrigação financeira identificável ou um fato econômico de receita/despesa.

Transaction não representa intenção genérica de orçamento, projeção,
cenário, transferência entre contas próprias ou simples movimentação
patrimonial.

Deve permitir representar pelo menos:

- receita;
- despesa;
- competência;
- vencimento;
- descrição;
- categoria;
- subcategoria;
- valor econômico nominal;
- cancelamento;
- estorno;
- observações.

Settlement representa a liquidação financeira efetiva de uma Transaction.

Uma Transaction pode possuir zero, um ou vários Settlements. Settlement
identifica conta, valor e data da liquidação e é o evento que afeta o saldo
da conta. Valores liquidado e remanescente são derivados e não devem ser
armazenados redundantemente.

Transfer representa movimentação direta entre contas próprias e permanece
separada de Transaction e Settlement.

A modelagem definitiva deve ser documentada em DATA_MODEL.md antes
de migrations relevantes.

---

## 8. Categorias e Meios de Pagamento

Categoria representa a natureza econômica do lançamento.

Exemplo:

Alimentação > Supermercado

Conta ou cartão representa onde ocorreu financeiramente.

Exemplo:

Cartão Nubank

Nunca utilizar cartão ou instituição financeira como substituto
automático para categoria de despesa.

---

## 9. Parcelamentos

Uma compra parcelada deve possuir uma entidade de origem.

Exemplo:

Notebook
Valor total: R$ 6.000
10 parcelas de R$ 600

Não cadastrar manualmente dez despesas independentes sem relacionamento.

As parcelas devem manter vínculo com o parcelamento que as originou.

---

## 10. Recorrências

Movimentações recorrentes devem possuir uma definição de recorrência.

Exemplos:

- salário;
- academia;
- aluguel;
- assinatura;
- contribuição mensal.

Não duplicar indefinidamente registros sem preservar a origem da
recorrência.

---

## 11. Dívidas

Dívidas devem ser tratadas separadamente de despesas comuns quando
necessário.

A arquitetura deve permitir armazenar:

- credor;
- descrição;
- valor original;
- saldo devedor;
- data de contratação;
- taxa;
- quantidade de parcelas;
- vencimentos;
- parcelas;
- pagamentos;
- status.

O saldo devedor deve possuir regra de cálculo claramente documentada.

---

## 12. Orçamento

O orçamento representa intenção financeira.

Deve permitir comparação entre:

ORÇADO
vs
COMPROMETIDO
vs
REALIZADO

por:

- período;
- categoria;
- subcategoria.

O sistema deve suportar visão mensal e anual.

---

## 13. Mapa Anual

O Aurora Finance deverá possuir uma visão anual semelhante conceitualmente
à planilha que originou o projeto.

Formato esperado:

Categoria | Jan | Fev | Mar | ... | Dez | Total

Essa visualização deve ser gerada dinamicamente a partir dos dados.

Nunca criar estruturas específicas para cada ano.

---

## 14. Planejamento e Cenários

Cenários NÃO devem alterar os dados financeiros reais.

Exemplo:

Cenário:
"Consultoria a partir de novembro"

Pode adicionar hipoteticamente:

- R$ 4.000/mês

As projeções do cenário são calculadas separadamente.

Excluir um cenário não pode remover ou modificar movimentações reais.

---

## 15. Aurora Insights

Aurora Insights será o motor de inteligência financeira.

Primeira implementação deve utilizar regras determinísticas.

Exemplos:

- comprometimento da renda;
- evolução das despesas;
- compromissos futuros;
- variações relevantes;
- runway financeiro;
- concentração de despesas;
- evolução patrimonial.

IA generativa poderá ser adicionada posteriormente.

Cálculos financeiros não devem depender de IA generativa.

---

## 16. Interface

A interface deve priorizar:

- clareza;
- baixa poluição visual;
- hierarquia de informação;
- consistência;
- leitura rápida;
- responsividade quando possível.

Evitar dashboards carregados de gráficos sem finalidade.

Todo indicador deve responder a uma pergunta financeira.

---

## 17. Idioma e Formatação

Interface:

Português do Brasil.

Moeda padrão:

BRL.

Formato visual:

R$ 1.234,56

Datas:

DD/MM/AAAA

Internamente, datas e valores devem utilizar tipos adequados e não
strings formatadas.

---

## 18. Precisão Monetária

Não utilizar float para valores monetários persistidos.

Utilizar Decimal / Numeric com precisão adequada.

Arredondamentos devem possuir regras explícitas quando necessários.

---

## 19. Segurança

Nunca versionar:

- senhas;
- tokens;
- chaves;
- arquivos .env reais;
- banco pessoal de produção;
- exports financeiros privados.

.env deve permanecer no .gitignore.

Manter apenas .env.example no repositório.

---

## 20. Git

Commits devem ser pequenos e semanticamente coerentes.

Preferir padrão:

feat:
fix:
refactor:
docs:
test:
chore:

Exemplos:

feat: add account domain model

feat: implement transaction service

fix: correct monthly balance calculation

docs: document transaction lifecycle

---

## 21. Testes

Regras financeiras críticas devem possuir testes.

Prioridade:

1. movimentações;
2. transferências;
3. parcelamentos;
4. recorrências;
5. orçamento;
6. dívidas;
7. projeções;
8. cenários.

Interface visual não substitui testes das regras de negócio.

---

## 22. Documentação

Antes de grandes alterações arquiteturais, verificar:

- ARCHITECTURE.md
- BUSINESS_RULES.md
- DATA_MODEL.md
- ROADMAP.md
- AGENTS.md

Quando uma alteração modificar uma regra documentada, atualizar também
a documentação correspondente.

---

## 23. Restrições do Agente

O agente NÃO deve:

- alterar arquitetura estrutural sem necessidade;
- criar novas dependências sem justificativa;
- substituir tecnologias principais sem autorização;
- remover migrations existentes arbitrariamente;
- apagar dados para resolver problemas;
- modificar regras financeiras silenciosamente;
- implementar funcionalidades fora do escopo solicitado;
- armazenar valores calculados apenas para facilitar a interface;
- duplicar lógica financeira entre páginas;
- colocar regras de negócio complexas diretamente no Streamlit;
- realizar refatorações amplas não solicitadas durante correções pequenas.

Quando existir ambiguidade financeira relevante, perguntar antes de
assumir uma regra.

---

## 24. Princípio de Implementação

Antes de implementar uma tarefa:

1. entender a regra;
2. identificar as entidades envolvidas;
3. verificar documentação existente;
4. implementar a menor solução coerente;
5. testar;
6. atualizar documentação quando necessário;
7. informar claramente o que foi alterado.

Não antecipar funcionalidades futuras apenas porque a arquitetura
permite implementá-las.

---

## 25. Prioridade Atual

A prioridade inicial é a versão:

Aurora Finance v0.1 — Foundation

Escopo:

- configuração do projeto;
- conexão com banco;
- SQLAlchemy;
- Alembic;
- modelos fundamentais;
- categorias;
- contas;
- estrutura inicial de movimentações;
- estrutura inicial de liquidações;
- services/repositories correspondentes;
- testes da fundação.

Não iniciar Dashboard, Insights, investimentos ou cenários antes que
a fundação esteja consistente.
