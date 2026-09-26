# Aurora Finance — Arquitetura de Produção

Status: decisão arquitetural para implementação no PROMPT #020  
Escopo: topologia e readiness; nenhum provedor ou deploy foi criado

## 1. Decisão

O Aurora Finance deverá ser publicado sob **uma única origem HTTPS**, com
roteamento por caminho na borda da plataforma:

```text
Browser
  |
  | HTTPS — https://app.example.com
  v
Edge / roteador gerenciado
  |-- / e /assets/*  -> frontend React/Vite estático
  `-- /api/*         -> serviço FastAPI privado atrás do edge
                              |
                              `-> PostgreSQL gerenciado
```

O hostname é conceitual. O domínio e o fornecedor serão escolhidos no #020.
O componente de edge pode ser um recurso nativo da plataforma; não há decisão
por Nginx ou Caddy. Sua capacidade obrigatória é rotear caminhos preservando
host, scheme e IP de origem por headers encaminhados confiáveis.

Nesta topologia, **GitHub Pages não é necessário nem recomendado**. Ele não
oferece, por si só, o roteamento `/api/*` para o backend na mesma origem. O
repositório continua no GitHub, mas a hospedagem estática deve ficar em uma
plataforma/edge que componha frontend e API sob a mesma origem.

## 2. Por que uma origem

Uma origem única elimina CORS no tráfego público normal e evita cookie
cross-site. O cookie de sessão continua opaco, HttpOnly e restrito ao caminho
da API. CSRF e validação de `Origin` permanecem como defesa em profundidade.
Isso reduz diferenças entre navegadores, configuração de credenciais e
dependência de cookies de terceiros sem reduzir a segurança.

Prioridades atendidas:

1. segurança: HTTPS, cookie first-party e boundaries claros;
2. simplicidade: uma origem e um contrato `/api/v1`;
3. confiabilidade: serviços gerenciados e backup obrigatório;
4. baixo custo: frontend estático e um serviço pequeno, sem Redis ou proxy próprio;
5. recuperação: PostgreSQL com backup e restore verificáveis;
6. manutenção: migrations e comandos administrativos como jobs únicos;
7. evolução: frontend, API e banco continuam componentes independentes.

## 3. Alternativas consideradas

| Critério | GitHub Pages + API em site distinto | `app.` + `api.` no mesmo domínio registrável | Origem única com `/api/*` |
|---|---|---|---|
| Cookie | pode ser cross-site | same-site, mas cross-origin | first-party e same-origin |
| SameSite | frequentemente `None` | `Lax` é possível sob HTTPS | `Lax` recomendado |
| CSRF | obrigatório | obrigatório | obrigatório em profundidade |
| CORS | obrigatório | obrigatório | dispensável em produção |
| Domínio | dois sites e possível domínio customizado | dois subdomínios | um hostname |
| HTTPS | necessário nos dois hosts | necessário nos dois hosts | uma entrada pública |
| Deploy | dois destinos sem composição | dois serviços e DNS | edge + dois origins internos |
| Complexidade | alta para cookies | média | menor |
| Custo | estático barato; custo de integração | baixo/médio | baixo/médio |
| Manutenção | política cross-site sensível | CORS e proxy awareness | roteamento centralizado |
| Observabilidade | fragmentada | correlacionável por request ID | correlação direta no edge/API |
| Compatibilidade atual | suportada, mas endurece cookies | alta | alta, com configuração relativa |

A alternativa por subdomínios é o fallback se a plataforma escolhida não
suportar roteamento por caminho. Deve preservar o mesmo domínio registrável e
HTTPS para manter os requests same-site, embora CORS ainda seja necessário.
GitHub Pages com hostname `github.io` e API de outro site é a última opção.

## 4. Fluxos e boundaries de segurança

### Request

```text
Browser -> TLS/edge -> arquivo estático ou /api/* -> FastAPI -> PostgreSQL
```

- somente o edge é público;
- o banco não aceita conexões da internet aberta;
- o backend aceita tráfego apenas do edge/rede da plataforma quando possível;
- o frontend nunca recebe `DATABASE_URL` ou outro secret;
- o edge não deve registrar bodies financeiros ou headers de autenticação.

### Autenticação

```text
POST /api/v1/auth/login + Origin
-> Argon2id
-> AuthSession no PostgreSQL (somente hash do token)
-> Set-Cookie opaco HttpOnly
-> CSRF token em memória no React
-> mutações: cookie + Origin + X-CSRF-Token
```

Logout revoga a sessão no banco e expira o cookie. Não haverá signup público.
O cliente nunca escolhe `user_id`.

## 5. Cookie, CSRF e CORS

Política de produção recomendada:

- host-only: omitir `Domain`;
- `Path=/api/v1`;
- `HttpOnly=true`;
- `Secure=true`;
- `SameSite=Lax`;
- `Max-Age` igual à expiração server-side, inicialmente 12 horas;
- logout com os mesmos atributos de escopo.

`Strict` pode prejudicar entradas legítimas vindas de links externos e não é
necessário com as defesas atuais. `None` permanece suportado apenas para uma
eventual topologia realmente cross-site e sempre exige `Secure`.

Na origem única, o navegador não precisa de headers CORS em produção. A
allowlist configurada continua sendo usada pela validação de `Origin` do login
e das mutações. A middleware CORS pode permanecer com a origem pública exata,
sem wildcard, como compatibilidade defensiva; ela não é a proteção principal.
Desenvolvimento continua cross-origin entre portas locais e exige CORS.

## 6. TLS e proxy

O edge deve:

- obter e renovar o certificado automaticamente;
- aceitar apenas HTTPS para a aplicação e redirecionar HTTP para HTTPS;
- usar TLS moderno;
- encaminhar `X-Forwarded-Proto`, `X-Forwarded-Host` e `X-Forwarded-For`;
- remover headers encaminhados recebidos diretamente do cliente;
- preservar `X-Request-ID` ou gerar um quando ausente;
- encaminhar `/api/*` sem duplicar ou remover `/api/v1` indevidamente.

Uvicorn deve confiar em forwarded headers somente dos IPs/redes do proxy da
plataforma, nunca irrestritamente da internet. O reconhecimento do scheme
externo HTTPS deve ser validado no smoke do #020. Não serão gerados
certificados manualmente.

## 7. Frontend

- build: `npm ci` seguido de `npm run build`;
- `VITE_BASE_PATH=/` para hospedagem na raiz;
- `VITE_API_BASE_URL=/api/v1` para chamadas same-origin;
- `VITE_*` contém apenas configuração pública;
- `index.html`: revalidação curta/sem cache imutável;
- assets com hash: cache público longo e `immutable`;
- fallback de SPA preservado quando necessário.

O `HashRouter` permanece nesta etapa: funciona na nova topologia e não exige
fallback para cada rota. `BrowserRouter` passa a ser possível quando o edge
oferecer fallback confiável para `index.html`, mas a troca não traz benefício
financeiro ou de segurança suficiente antes do primeiro deploy.

## 8. Backend

Comando conceitual inicial:

```text
python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
```

Requisitos:

- um processo/worker inicial é suficiente para uso pessoal;
- escala horizontal somente após necessidade medida;
- shutdown gracioso fornecido pelo runtime ASGI e pela plataforma;
- nenhuma migration no startup de cada worker;
- `AURORA_ENV=production` e validação fail-fast da configuração;
- proxy awareness limitada aos proxies confiáveis;
- `/api/v1/health` como liveness inicial, sem secrets ou detalhes internos.

O health atual prova que o processo FastAPI responde. Readiness de banco pode
ser verificada pelo mecanismo da plataforma ou por um endpoint futuro separado
somente se o provedor exigir. Misturar query de banco no liveness poderia
reiniciar uma API saudável durante indisponibilidade transitória do banco.

Uvicorn já é suficiente. Gunicorn não é requisito. Container é recomendado
somente se o provedor escolhido usar imagem como unidade nativa: aumenta a
reprodutibilidade, mas também manutenção. Plataformas com buildpack/runtime
Python gerenciado podem usar o projeto sem Docker.

## 9. PostgreSQL

O fornecedor deverá oferecer:

- PostgreSQL compatível com a versão 17 validada;
- TLS em trânsito e criptografia em repouso;
- conexão privada com o backend quando possível;
- backups automáticos e recuperação point-in-time quando disponível;
- retenção mínima de 14 dias para v1;
- restore para instância separada;
- região próxima ao usuário e ao backend;
- limites de conexão compatíveis com o pool e workers escolhidos;
- métricas básicas de conexão, armazenamento e disponibilidade;
- exportação lógica sem lock-in.

`DATABASE_URL` usa `postgresql+psycopg`, reside somente no secret manager do
backend e nunca aparece no frontend, repositório, respostas ou logs. Parâmetros
TLS serão definidos conforme o certificado e a política do fornecedor.

## 10. Migrations, deploy e rollback

Ordem do deploy:

```text
backup/verificação -> build -> migration job único -> backend -> frontend -> smoke
```

`alembic upgrade head` deve rodar como release command, job único ou etapa
controlada de pipeline. Nunca simultaneamente em cada worker. O pipeline deve
falhar antes de trocar tráfego se a migration falhar.

Rollback tem três decisões distintas:

- código: reimplantar o artefato anterior quando compatível com o schema;
- migration: somente downgrade explicitamente testado e considerado seguro;
- dados: restore/PITR quando uma migration destrutiva ou corrupção exigir.

Downgrade automático não é política. Mudanças futuras devem preferir migrations
expansíveis e compatíveis entre versões durante a janela de rollout.

## 11. Backup e recuperação

Para o primeiro uso em produção:

- backup gerenciado automático diário;
- retenção mínima de 14 dias;
- PITR preferível;
- exportação lógica portátil criptografada, periódica e independente do provedor;
- acesso aos backups limitado à operação administrativa;
- teste de restore trimestral em banco isolado;
- registro de RPO/RTO reais após escolha do provedor.

Backup do provedor protege a operação daquele serviço. Exportação lógica
portátil permite migração e recuperação fora dele; um não substitui o outro.

## 12. Secrets e configuração

| Item | Classe | Destino |
|---|---|---|
| `DATABASE_URL` | SECRET | secret manager/environment do backend |
| senha inicial/administrativa | SECRET efêmero | entrada interativa no job administrativo |
| credenciais de backup/exportação | SECRET | secret manager/job de backup |
| `AURORA_ENV` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| `CORS_ALLOWED_ORIGINS` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| `AUTH_SESSION_HOURS` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| `AUTH_COOKIE_NAME` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| `AUTH_COOKIE_SECURE` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| `AUTH_COOKIE_SAMESITE` | CONFIGURAÇÃO NÃO SECRETA | environment do backend |
| proxy trusted IPs/networks | CONFIGURAÇÃO NÃO SECRETA | comando/runtime do backend |
| `VITE_API_BASE_URL` | BUILD-TIME FRONTEND | pipeline de build |
| `VITE_BASE_PATH` | BUILD-TIME FRONTEND | pipeline de build |

O CI/CD futuro recebe somente os secrets estritamente necessários e não os
imprime. Build frontend nunca recebe secrets.

## 13. Administração de usuário e sessões

`python -m scripts.provision_user` será executado como console/job administrativo
one-off na mesma release do backend, com `DATABASE_URL` injetada pelo secret
manager e senha fornecida interativamente. Não deve aparecer em argumento de
linha de comando, histórico ou log.

Para v1, recuperação por email não é necessária. Antes do go-live deve existir
um fluxo CLI administrativo testado para redefinir a senha e revogar todas as
sessões do usuário. Uma tela autenticada de alteração de senha pode ficar para
depois da v1.

Sessões expiradas não autenticam, mas ocupam armazenamento. Uma limpeza simples
periódica — job do provedor ou comando administrativo diário/semanal — deverá
remover sessões expiradas e, após retenção operacional curta, revogadas. Não há
justificativa para scheduler ou Redis dedicado.

## 14. Rate limiting

Rate limiting de login é requisito antes do go-live. Preferência:

- proteção no edge/provedor por IP e rota;
- limites moderados com janela e bloqueio temporário;
- resposta genérica, sem enumeração de usuários;
- métricas sem senha, cookie ou payload;
- teste para não bloquear o uso legítimo.

Não adicionar Redis apenas para isso. Se o edge escolhido não fornecer proteção
adequada, implementar limite local compatível com uma única instância antes de
publicar e reavaliar ao escalar horizontalmente.

## 15. Observabilidade e headers

Mínimo para v1:

- logs estruturados de startup, shutdown, status e erro;
- request ID propagado edge -> FastAPI -> resposta;
- eventos de login bem-sucedido/falho, logout e revogação sem identificadores
  sensíveis desnecessários;
- métricas simples de latência, taxa de erro, reinício, CPU/memória, conexões e
  armazenamento;
- alerta básico para indisponibilidade e falha de backup.

Nunca registrar senha, cookie, token de sessão, CSRF token, `DATABASE_URL` ou
payload financeiro completo.

Headers preferencialmente definidos no edge, que atende frontend e API:

- `Strict-Transport-Security` após HTTPS e domínio estarem confirmados;
- `Content-Security-Policy` específica para os assets e API same-origin;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- `frame-ancestors 'none'` na CSP; `X-Frame-Options: DENY` como compatibilidade;
- `Permissions-Policy` restritiva às capacidades realmente usadas.

O FastAPI mantém `X-Request-ID` e políticas específicas da API. Evitar definir
o mesmo header com valores conflitantes nas duas camadas.

## 16. Matriz de ambientes

| Tema | Development | Test | Production |
|---|---|---|---|
| Banco | SQLite local | SQLite isolado; PostgreSQL opt-in | PostgreSQL gerenciado |
| Frontend | Vite `localhost:5173` | jsdom/build; smoke local | estático em `/` |
| API | `localhost:8000` | TestClient/servidor efêmero | `/api/*` na mesma origem |
| Cookie | host-only, `Lax`, sem `Secure` em HTTP local | host-only, `Lax` | host-only, `Lax`, `Secure`, HttpOnly |
| CORS | origem local explícita | origem de teste explícita | não necessário no fluxo normal; sem wildcard |
| CSRF/Origin | obrigatórios | obrigatórios | obrigatórios |
| HTTPS | opcional localmente | conforme smoke | obrigatório no edge |
| Secrets | `.env` ignorado | fixtures/env efêmeros | secret manager do backend |
| Migrations | comando manual | banco isolado | job único de release |

## 17. Critérios para escolher o fornecedor no #020

O fornecedor/topologia concreta deve demonstrar:

- roteamento same-origin por caminho;
- TLS e redirect gerenciados;
- serviço Python com comando e health configuráveis;
- secret manager;
- job/release command one-off;
- PostgreSQL 17 compatível, privado e com backup/PITR;
- restore e exportação;
- logs/métricas básicas;
- rate limiting no edge ou mecanismo equivalente;
- região adequada e custo previsível para uso pessoal;
- portabilidade dos dados e ausência de lock-in incontornável.

