# Aurora Finance — Checklist de Produção

Status: preparado para execução no PROMPT #020. Nenhum item dependente de
infraestrutura real está marcado como concluído.

## Infraestrutura

- [ ] Escolher fornecedor conforme `PRODUCTION_ARCHITECTURE.md`.
- [ ] Confirmar roteamento de `/`, `/assets/*` e `/api/*` na mesma origem.
- [ ] Escolher região próxima para frontend, backend e PostgreSQL.
- [ ] Restringir backend à borda/rede da plataforma quando possível.
- [ ] Registrar custo e limites do plano escolhido.

## Database

- [ ] Criar PostgreSQL gerenciado compatível com PostgreSQL 17.
- [ ] Exigir TLS, criptografia em repouso e acesso privado quando possível.
- [ ] Configurar limites de conexão coerentes com um worker inicial.
- [ ] Confirmar métricas de conexões, armazenamento e disponibilidade.
- [ ] Confirmar capacidade de exportação lógica.

## Backend

- [ ] Configurar start command Uvicorn, host `0.0.0.0` e porta da plataforma.
- [ ] Iniciar com um worker; não fazer tuning sem medição.
- [ ] Configurar proxy trusted IPs/networks.
- [ ] Validar shutdown gracioso.
- [ ] Confirmar que docs/OpenAPI públicos estão desabilitados em produção.
- [ ] Confirmar que `/api/v1/health` não expõe detalhes internos.

## Frontend

- [ ] Usar `npm ci` e build reproduzível.
- [ ] Definir `VITE_BASE_PATH=/`.
- [ ] Definir `VITE_API_BASE_URL=/api/v1`.
- [ ] Configurar cache curto para `index.html`.
- [ ] Configurar cache longo e imutável para assets com hash.
- [ ] Validar rotas hash e refresh direto.

## Auth

- [ ] Provisionar o usuário via job/console administrativo one-off.
- [ ] Não criar signup público.
- [ ] Implementar/testar reset administrativo de senha com revogação de sessões.
- [ ] Confirmar Argon2id e persistência apenas do hash de sessão.
- [ ] Configurar rate limiting de login no edge antes do go-live.
- [ ] Criar limpeza simples e periódica de sessões expiradas/revogadas.

## Cookies

- [ ] Confirmar host-only, sem atributo `Domain`.
- [ ] Confirmar `Path=/api/v1`.
- [ ] Confirmar `HttpOnly`, `Secure` e `SameSite=Lax`.
- [ ] Confirmar `Max-Age` alinhado à expiração server-side.
- [ ] Validar logout com os mesmos atributos de escopo.
- [ ] Testar em navegadores modernos suportados.

## CSRF

- [ ] Confirmar `Origin` no login e em todas as mutações.
- [ ] Confirmar `X-CSRF-Token` nas mutações autenticadas.
- [ ] Confirmar que token CSRF fica somente em memória no frontend.
- [ ] Executar testes negativos de Origin e CSRF no ambiente implantado.

## CORS

- [ ] Usar somente a origem HTTPS pública exata na allowlist.
- [ ] Não usar wildcard com credentials.
- [ ] Confirmar que o tráfego same-origin não depende de CORS.
- [ ] Se houver fallback por subdomínios, validar preflight e credentials.

## TLS

- [ ] Emitir e renovar certificado pela plataforma.
- [ ] Redirecionar HTTP para HTTPS.
- [ ] Validar `X-Forwarded-Proto`, host e IP via proxy confiável.
- [ ] Confirmar que FastAPI reconhece o scheme público HTTPS.
- [ ] Ativar HSTS somente após validar domínio e HTTPS.

## Secrets

- [ ] Armazenar `DATABASE_URL` apenas no secret manager do backend.
- [ ] Não fornecer secrets ao build frontend.
- [ ] Não imprimir secrets em build, release command ou logs.
- [ ] Revisar permissões de operadores e CI/CD.
- [ ] Executar scan final do repositório e artefatos.

## Migrations

- [ ] Obter/verificar backup antes de migration relevante.
- [ ] Executar `alembic upgrade head` uma única vez como release job.
- [ ] Impedir migrations concorrentes por workers.
- [ ] Verificar `alembic current` e `alembic check` após o deploy.
- [ ] Testar compatibilidade do código anterior antes de autorizar rollback.

## Backup

- [ ] Ativar backup automático diário e retenção mínima de 14 dias.
- [ ] Ativar PITR quando disponível.
- [ ] Definir RPO e RTO reais.
- [ ] Configurar exportação lógica portátil e criptografada.
- [ ] Executar restore inicial em instância isolada.
- [ ] Agendar teste trimestral de restore.

## Observability

- [ ] Propagar `X-Request-ID` do edge à API e resposta.
- [ ] Habilitar logs de aplicação sem payload financeiro ou credenciais.
- [ ] Confirmar redaction de senha, cookie, tokens, CSRF e `DATABASE_URL`.
- [ ] Monitorar latência, erros, reinícios e recursos básicos.
- [ ] Alertar indisponibilidade e falha de backup.

## Security headers

- [ ] Definir CSP same-origin no edge.
- [ ] Definir `X-Content-Type-Options: nosniff`.
- [ ] Definir `Referrer-Policy: strict-origin-when-cross-origin`.
- [ ] Definir `frame-ancestors 'none'` e compatibilidade de frame protection.
- [ ] Definir `Permissions-Policy` mínima.
- [ ] Evitar valores conflitantes entre edge e FastAPI.

## Smoke

- [ ] Validar health público por HTTPS.
- [ ] Login, `/auth/me`, conta, categoria, Transaction e Settlement.
- [ ] Validar summaries por competência, vencimento e caixa.
- [ ] Reexecutar o caso temporal `2026-09-23T02:30:00Z`.
- [ ] Validar logout, revogação, sessão expirada, CSRF e ownership A/B.
- [ ] Validar que nenhum secret aparece em resposta ou log.
- [ ] Executar suíte backend, PostgreSQL e frontend contra a release.

## Rollback

- [ ] Manter artefato anterior identificável.
- [ ] Documentar compatibilidade do artefato anterior com o schema novo.
- [ ] Não executar downgrade de banco automaticamente.
- [ ] Validar procedimento de restore/PITR.
- [ ] Definir critério de abortar deploy e critério de rollback.

## Go-live

- [ ] Todos os itens obrigatórios acima concluídos e evidenciados.
- [ ] Nenhum dado pessoal usado no smoke inicial.
- [ ] Aprovação humana explícita para publicação.
- [ ] Decisão separada sobre aposentadoria do Streamlit após estabilidade.

