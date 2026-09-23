# Aurora Finance

Aurora Finance é uma plataforma pessoal de gestão, planejamento e inteligência financeira. Este repositório está na fase **v0.1 — Foundation**, com a infraestrutura técnica e os primeiros modelos de cadastro.

## Stack

- Python 3.12
- Streamlit
- SQLAlchemy
- Alembic
- SQLite
- Pandas
- Plotly
- Pytest

## Requisitos

- Python 3.12 ou uma versão compatível
- `pip`

## Configuração local

Crie e ative um ambiente virtual:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Copie a configuração de exemplo e ajuste-a apenas se necessário:

```powershell
Copy-Item .env.example .env
```

O valor padrão usa um arquivo SQLite local:

```dotenv
DATABASE_URL=sqlite:///aurora_finance.db
```

O arquivo `.env` e bancos SQLite locais são ignorados pelo Git.

## Executar a aplicação

```powershell
streamlit run app.py
```

A interface atual é apenas a inicialização mínima da aplicação; ainda não existem páginas financeiras funcionais.

## Executar os testes

```powershell
python -m pytest
```

Os testes criam bancos SQLite temporários e não utilizam o banco pessoal da aplicação.

## Alembic

Verifique o estado das migrations:

```powershell
python -m alembic current
```

Crie uma revisão depois de uma alteração aprovada nos modelos:

```powershell
python -m alembic revision --autogenerate -m "descrição da alteração"
```

Aplique as migrations existentes:

```powershell
python -m alembic upgrade head
```

Reverta a última migration:

```powershell
python -m alembic downgrade -1
```

A migration inicial cria exclusivamente as tabelas fundamentais `users`, `accounts`, `categories` e `subcategories`.
